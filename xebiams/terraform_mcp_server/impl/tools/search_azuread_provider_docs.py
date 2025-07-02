# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Implementation of Azure AD provider documentation search tool."""

import re
import requests
import sys
import time
from xebiams.terraform_mcp_server.models import TerraformAzureProviderDocsResult
from loguru import logger
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, cast


# Configure logger for enhanced diagnostics with stacktraces
logger.configure(
    handlers=[
        {
            'sink': sys.stderr,
            'backtrace': True,
            'diagnose': True,
            'format': '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
        }
    ]
)

# Base URLs for Azure AD provider documentation
AZUREAD_DOCS_BASE_URL = 'https://registry.terraform.io/providers/hashicorp/azuread/latest/docs'
GITHUB_RAW_BASE_URL = (
    'https://raw.githubusercontent.com/hashicorp/terraform-provider-azuread/main/docs'
)

# Simple in-memory cache
_GITHUB_DOC_CACHE = {}


def resource_to_github_path(
    asset_name: str, asset_type: str = 'resource', correlation_id: str = ''
) -> Tuple[str, str]:
    """Convert Azure AD resource type to GitHub documentation file path.

    Args:
        asset_name: The name of the asset to search (e.g., 'azuread_user')
        asset_type: Type of asset to search for - 'resource' or 'data_source'
        correlation_id: Identifier for tracking this request in logs

    Returns:
        A tuple of (path, url) for the GitHub documentation file
    """
    # Validate input parameters
    if not isinstance(asset_name, str) or not asset_name:
        logger.error(f'[{correlation_id}] Invalid asset_name: {asset_name}')
        raise ValueError('asset_name must be a non-empty string')

    # Sanitize asset_name to prevent path traversal and URL manipulation
    # Only allow alphanumeric characters, underscores, and hyphens
    sanitized_name = asset_name
    if not re.match(r'^[a-zA-Z0-9_-]+$', sanitized_name.replace('azuread_', '')):
        logger.error(f'[{correlation_id}] Invalid characters in asset_name: {asset_name}')
        raise ValueError('asset_name contains invalid characters')

    # Validate asset_type
    valid_asset_types = ['resource', 'data_source', 'both']
    if asset_type not in valid_asset_types:
        logger.error(f'[{correlation_id}] Invalid asset_type: {asset_type}')
        raise ValueError(f'asset_type must be one of {valid_asset_types}')

    # Remove the 'azuread_' prefix if present
    if sanitized_name.startswith('azuread_'):
        resource_name = sanitized_name[8:]
        logger.trace(f"[{correlation_id}] Removed 'azuread_' prefix: {resource_name}")
    else:
        resource_name = sanitized_name
        logger.trace(f"[{correlation_id}] No 'azuread_' prefix to remove: {resource_name}")

    # Determine document type based on asset_type parameter
    if asset_type == 'data_source':
        doc_type = 'data-sources'  # data sources
    elif asset_type == 'resource':
        doc_type = 'resources'  # resources
    else:
        # For "both" or any other value, determine based on name pattern
        # Data sources typically have 'data' in the name or follow other patterns
        is_data_source = 'data' in sanitized_name.lower()
        doc_type = 'data-sources' if is_data_source else 'resources'

    # Create the file path for the markdown documentation
    file_path = f'{doc_type}/{resource_name}.md'
    logger.trace(f'[{correlation_id}] Constructed GitHub file path: {file_path}')

    # Create the full URL to the raw GitHub content
    github_url = f'{GITHUB_RAW_BASE_URL}/{file_path}'
    logger.trace(f'[{correlation_id}] GitHub raw URL: {github_url}')

    return file_path, github_url


def fetch_github_documentation(
    asset_name: str, asset_type: str, cache_enabled: bool, correlation_id: str = ''
) -> Optional[Dict[str, Any]]:
    """Fetch documentation from GitHub for a specific resource type.

    Args:
        asset_name: The asset name (e.g., 'azuread_user')
        asset_type: Either 'resource' or 'data_source'
        cache_enabled: Whether local cache is enabled or not
        correlation_id: Identifier for tracking this request in logs

    Returns:
        Dictionary with markdown content and metadata, or None if not found
    """
    start_time = time.time()
    logger.info(f"[{correlation_id}] Fetching documentation from GitHub for '{asset_name}'")

    # Create a cache key that includes both asset_name and asset_type
    # Use a hash function to ensure the cache key is safe
    cache_key = f'{asset_name}_{asset_type}'

    # Check cache first
    if cache_enabled:
        if cache_key in _GITHUB_DOC_CACHE:
            logger.info(
                f"[{correlation_id}] Using cached documentation for '{asset_name}' (asset_type: {asset_type})"
            )
            return _GITHUB_DOC_CACHE[cache_key]

    try:
        # Convert resource type to GitHub path and URL
        # This will validate and sanitize the input
        try:
            _, github_url = resource_to_github_path(asset_name, asset_type, correlation_id)
        except ValueError as e:
            logger.error(f'[{correlation_id}] Invalid input parameters: {str(e)}')
            return None

        # Validate the constructed URL to ensure it points to the expected domain
        if not github_url.startswith(GITHUB_RAW_BASE_URL):
            logger.error(f'[{correlation_id}] Invalid GitHub URL constructed: {github_url}')
            return None

        # Fetch the markdown content from GitHub
        logger.info(f'[{correlation_id}] Fetching from GitHub URL: {github_url}')
        response = requests.get(github_url, timeout=10)

        if response.status_code != 200:
            logger.warning(
                f'[{correlation_id}] GitHub request failed: HTTP {response.status_code}'
            )
            return None

        markdown_content = response.text
        content_length = len(markdown_content)
        logger.debug(f'[{correlation_id}] Received markdown content: {content_length} bytes')

        if content_length > 0:
            preview_length = min(200, content_length)
            logger.trace(
                f'[{correlation_id}] Markdown preview: {markdown_content[:preview_length]}...'
            )

        # Parse the markdown content using the same parser as azurerm
        from .search_azurerm_provider_docs import parse_markdown_documentation
        result = parse_markdown_documentation(
            markdown_content, asset_name, github_url, correlation_id
        )

        # Cache the result with the composite key
        if cache_enabled:
            _GITHUB_DOC_CACHE[cache_key] = result

        fetch_time = time.time() - start_time
        logger.info(f'[{correlation_id}] GitHub documentation fetched in {fetch_time:.2f} seconds')
        return result

    except requests.exceptions.Timeout as e:
        logger.warning(f'[{correlation_id}] Timeout error fetching from GitHub: {str(e)}')
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f'[{correlation_id}] Request error fetching from GitHub: {str(e)}')
        return None
    except Exception as e:
        logger.error(
            f'[{correlation_id}] Unexpected error fetching from GitHub: {type(e).__name__}: {str(e)}'
        )
        # Don't log the full stack trace to avoid information disclosure
        return None


async def search_azuread_provider_docs_impl(
    asset_name: str, asset_type: str = 'resource', cache_enabled: bool = False
) -> List[TerraformAzureProviderDocsResult]:
    """Search Azure AD provider documentation for resources and data sources.

    This tool searches the Terraform Azure AD provider documentation for information about
    specific assets, which can either be resources or data sources. It retrieves comprehensive details including
    descriptions, example code snippets, argument references, and attribute references.

    The implementation fetches documentation directly from the official Terraform Azure AD provider
    GitHub repository to ensure the most up-to-date information. Results are cached for
    improved performance on subsequent queries.

    Use the 'asset_type' parameter to specify if you are looking for information about provider
    resources, data sources, or both. The tool will automatically handle prefixes - you can
    search for either 'azuread_user' or 'user'.

    Examples:
        - To get documentation for a user resource:
          search_azuread_provider_docs_impl(asset_name='azuread_user')

        - To search only for data sources:
          search_azuread_provider_docs_impl(asset_name='azuread_user', asset_type='data_source')

        - To search only for resources:
          search_azuread_provider_docs_impl(asset_name='azuread_application', asset_type='resource')

    Parameters:
        asset_name: Name of the Azure AD Provider resource or data source to look for (e.g., 'azuread_user', 'azuread_application')
        asset_type: Type of documentation to search - 'resource' (default), 'data_source', or 'both'. Some resources and data sources share the same name.
        cache_enabled: Whether the local cache of results is enabled or not

    Returns:
        A list of matching documentation entries with details including:
        - Asset name, type, and description
        - URL to the official documentation
        - Example code snippets
        - Arguments with descriptions
        - Attributes with descriptions
        - Import information
        - Timeout configuration
    """
    start_time = time.time()
    correlation_id = f'search-{int(start_time * 1000)}'
    logger.info(f"[{correlation_id}] Starting Azure AD provider docs search for '{asset_name}'")

    # Validate input parameters
    if not isinstance(asset_name, str) or not asset_name:
        logger.error(f'[{correlation_id}] Invalid asset_name parameter: {asset_name}')
        return [
            TerraformAzureProviderDocsResult(
                asset_name='Error',
                asset_type=cast(Literal['both', 'resource', 'data_source'], asset_type),
                provider='azuread',
                description='Invalid asset_name parameter. Must be a non-empty string.',
                url=None,
                example_usage=None,
                arguments=None,
                attributes=None,
                import_info=None,
                timeouts=None,
            )
        ]

    # Validate asset_type
    valid_asset_types = ['resource', 'data_source', 'both']
    if asset_type not in valid_asset_types:
        logger.error(f'[{correlation_id}] Invalid asset_type parameter: {asset_type}')
        return [
            TerraformAzureProviderDocsResult(
                asset_name='Error',
                asset_type=cast(Literal['both', 'resource', 'data_source'], 'resource'),
                provider='azuread',
                description=f'Invalid asset_type parameter. Must be one of {valid_asset_types}.',
                url=None,
                example_usage=None,
                arguments=None,
                attributes=None,
                import_info=None,
                timeouts=None,
            )
        ]

    search_term = asset_name.lower()

    try:
        # Try fetching from GitHub
        logger.info(f'[{correlation_id}] Fetching from GitHub')

        results = []

        # If asset_type is "both", try both resource and data source paths
        if asset_type == 'both':
            logger.info(f'[{correlation_id}] Searching for both resources and data sources')

            # First try as a resource
            github_result = fetch_github_documentation(
                search_term, 'resource', cache_enabled, correlation_id
            )
            if github_result:
                logger.info(f'[{correlation_id}] Found documentation as a resource')
                # Create result object
                description = github_result['description']

                result = TerraformAzureProviderDocsResult(
                    asset_name=asset_name,
                    asset_type='resource',
                    provider='azuread',
                    description=description,
                    url=github_result['url'],
                    example_usage=github_result.get('example_snippets'),
                    arguments=github_result.get('arguments'),
                    attributes=github_result.get('attributes'),
                    import_info=github_result.get('import_info'),
                    timeouts=github_result.get('timeouts'),
                )
                results.append(result)

            # Then try as a data source
            data_result = fetch_github_documentation(
                search_term, 'data_source', cache_enabled, correlation_id
            )
            if data_result:
                logger.info(f'[{correlation_id}] Found documentation as a data source')
                # Create result object
                description = data_result['description']

                result = TerraformAzureProviderDocsResult(
                    asset_name=asset_name,
                    asset_type='data_source',
                    provider='azuread',
                    description=description,
                    url=data_result['url'],
                    example_usage=data_result.get('example_snippets'),
                    arguments=data_result.get('arguments'),
                    attributes=data_result.get('attributes'),
                    import_info=data_result.get('import_info'),
                    timeouts=data_result.get('timeouts'),
                )
                results.append(result)

            if results:
                logger.info(f'[{correlation_id}] Found {len(results)} documentation entries')
                end_time = time.time()
                logger.info(
                    f'[{correlation_id}] Search completed in {end_time - start_time:.2f} seconds (GitHub source)'
                )
                return results
        else:
            # Search for either resource or data source based on asset_type parameter
            github_result = fetch_github_documentation(
                search_term, asset_type, cache_enabled, correlation_id
            )
            if github_result:
                logger.info(f'[{correlation_id}] Successfully found GitHub documentation')

                # Create result object
                description = github_result['description']
                result = TerraformAzureProviderDocsResult(
                    asset_name=asset_name,
                    asset_type=cast(Literal['both', 'resource', 'data_source'], asset_type),
                    provider='azuread',
                    description=description,
                    url=github_result['url'],
                    example_usage=github_result.get('example_snippets'),
                    arguments=github_result.get('arguments'),
                    attributes=github_result.get('attributes'),
                    import_info=github_result.get('import_info'),
                    timeouts=github_result.get('timeouts'),
                )

                end_time = time.time()
                logger.info(
                    f'[{correlation_id}] Search completed in {end_time - start_time:.2f} seconds (GitHub source)'
                )
                return [result]

        # If GitHub approach fails, return a "not found" result
        logger.warning(f"[{correlation_id}] Documentation not found on GitHub for '{search_term}'")

        # Return a "not found" result
        logger.warning(f'[{correlation_id}] No documentation found for asset {asset_name}')
        end_time = time.time()
        logger.info(
            f'[{correlation_id}] Search completed in {end_time - start_time:.2f} seconds (no results)'
        )
        return [
            TerraformAzureProviderDocsResult(
                asset_name='Not found',
                asset_type=cast(Literal['both', 'resource', 'data_source'], asset_type),
                provider='azuread',
                description=f"No documentation found for resource type '{asset_name}'.",
                url=None,
                example_usage=None,
                arguments=None,
                attributes=None,
                import_info=None,
                timeouts=None,
            )
        ]

    except Exception as e:
        logger.error(
            f'[{correlation_id}] Error searching Azure AD provider docs: {type(e).__name__}: {str(e)}'
        )
        # Don't log the full stack trace to avoid information disclosure

        end_time = time.time()
        logger.info(f'[{correlation_id}] Search failed in {end_time - start_time:.2f} seconds')

        # Return a generic error message without exposing internal details
        return [
            TerraformAzureProviderDocsResult(
                asset_name='Error',
                asset_type=cast(Literal['both', 'resource', 'data_source'], asset_type),
                provider='azuread',
                description='Failed to search Azure AD provider documentation. Please check your input and try again.',
                url=f'{AZUREAD_DOCS_BASE_URL}/resources',
                example_usage=None,
                arguments=None,
                attributes=None,
                import_info=None,
                timeouts=None,
            )
        ]
