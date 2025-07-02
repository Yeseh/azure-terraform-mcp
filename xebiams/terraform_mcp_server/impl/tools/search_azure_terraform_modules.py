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

"""Implementation of Azure-specific Terraform module search and analysis tool."""

import asyncio
import re
import requests
import time
import traceback
from .utils import (
    clean_description,
    extract_outputs_from_readme,
    get_github_release_details,
    get_submodules,
    get_variables_tf,
    parse_module_url,
)
from xebiams.terraform_mcp_server.models import ModuleSearchResult, SubmoduleInfo, TerraformVariable, TerraformOutput
from loguru import logger
from typing import Dict, List, Optional, Any


# Define popular Azure modules to check
AZURE_POPULAR_MODULES = [
    {'namespace': 'Azure', 'name': 'aks', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'app-service', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'application-gateway', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'compute', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'container-registry', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'cosmosdb', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'database', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'front-door', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'key-vault', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'load-balancer', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'network', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'storage', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'virtual-machine', 'provider': 'azurerm'},
    {'namespace': 'Azure', 'name': 'vnet', 'provider': 'azurerm'}
]


async def get_azure_module_details(namespace: str, name: str, provider: str = 'azurerm') -> Dict:
    """Fetch detailed information about a specific Azure Terraform module.

    Args:
        namespace: The module namespace (e.g., Azure, claranet)
        name: The module name (e.g., aks, storage)
        provider: The provider (default: azurerm, could be azuread or azapi)

    Returns:
        Dictionary containing module details including README content and submodules
    """
    logger.info(f'Fetching details for Azure module {namespace}/{name}/{provider}')

    try:
        # Get basic module info via API
        details_url = f'https://registry.terraform.io/v1/modules/{namespace}/{name}/{provider}'
        logger.debug(f'Making API request to: {details_url}')

        response = requests.get(details_url, timeout=10)
        response.raise_for_status()

        details = response.json()
        logger.debug(
            f'Received module details. Status code: {response.status_code}, Content size: {len(response.text)} bytes'
        )

        # Debug log the version info we initially have
        initial_version = details.get('latest_version', 'unknown')
        if 'latest' in details and 'version' in details['latest']:
            initial_version = details['latest']['version']
        logger.debug(f'Initial version from primary API: {initial_version}')

        # Add additional API call to get the latest version if not in details
        if 'latest' not in details or 'version' not in details.get('latest', {}):
            versions_url = f'{details_url}/versions'
            logger.debug(f'Making API request to get versions: {versions_url}')

            versions_response = requests.get(versions_url, timeout=10)
            logger.debug(f'Versions API response code: {versions_response.status_code}')

            if versions_response.status_code == 200:
                versions_data = versions_response.json()
                logger.debug(
                    f'Received versions data with {len(versions_data.get("modules", []))} module versions'
                )

                if versions_data.get('modules') and len(versions_data['modules']) > 0:
                    latest_version = versions_data['modules'][0].get('version', '')
                    details['latest_version'] = latest_version
                    logger.debug(f'Updated latest version to: {latest_version}')
                else:
                    logger.debug('No modules found in versions response')
            else:
                logger.debug(
                    f'Failed to fetch versions. Status code: {versions_response.status_code}'
                )
        else:
            logger.debug('Latest version already available in primary API response')

        # Try to get README content and version details
        readme_content = None
        version_details = None
        version_from_github = ''

        # APPROACH 1: Try to see if the registry API provides README content directly
        logger.debug('APPROACH 1: Checking for README content in API response')
        if 'readme' in details and details['readme']:
            readme_content = details['readme']
            logger.info(
                f'Found README content directly in API response: {len(readme_content)} chars'
            )

        # APPROACH 2: Try using the GitHub repo URL for README content and version details
        if 'source' in details:
            source_url = details.get('source')
            # Validate GitHub URL using regex to ensure it's from github.com domain
            if isinstance(source_url, str) and re.match(r'https://github.com/', source_url):
                logger.info(f'Found GitHub source URL: {source_url}')

                # Extract GitHub owner and repo
                github_parts = re.match(r'https://github.com/([^/]+)/([^/]+)', source_url)
                if github_parts:
                    owner, repo = github_parts.groups()
                    logger.info(f'Extracted GitHub repo: {owner}/{repo}')

                    # Get version details from GitHub
                    github_version_info = await get_github_release_details(owner, repo)
                    version_details = github_version_info['details']
                    version_from_github = github_version_info['version']

                    if version_from_github:
                        logger.info(f'Found version from GitHub: {version_from_github}')
                        details['latest_version'] = version_from_github

                    # Get variables.tf content and parsed variables for Azure modules
                    variables_content, variables = await get_azure_variables_tf(owner, repo, 'main')
                    if variables_content and variables:
                        logger.info(f'Found variables.tf with {len(variables)} variables')
                        details['variables_content'] = variables_content
                        details['variables'] = [var.dict() for var in variables]
                    else:
                        # Try master branch as fallback if main didn't work
                        variables_content, variables = await get_azure_variables_tf(
                            owner, repo, 'master'
                        )
                        if variables_content and variables:
                            logger.info(
                                f'Found variables.tf in master branch with {len(variables)} variables'
                            )
                            details['variables_content'] = variables_content
                            details['variables'] = [var.dict() for var in variables]

                    # If README content not already found, try fetching it from GitHub
                    if not readme_content:
                        logger.debug(
                            f'APPROACH 2: Fetching README from GitHub source: {source_url}'
                        )

                        # Try main branch first, then fall back to master if needed
                        found_readme_branch = None
                        for branch in ['main', 'master']:
                            raw_readme_url = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md'
                            logger.debug(f'Trying to fetch README from: {raw_readme_url}')

                            readme_response = requests.get(raw_readme_url, timeout=10)
                            if readme_response.status_code == 200:
                                readme_content = readme_response.text
                                found_readme_branch = branch
                                logger.info(
                                    f'Successfully fetched README from GitHub ({branch}): {len(readme_content)} chars'
                                )
                                break

                        # Look for submodules now that we have identified the main branch
                        if found_readme_branch:
                            logger.info(
                                f'Fetching submodules using {found_readme_branch} branch'
                            )
                            start_time = time.time()
                            submodules = await get_submodules(owner, repo, found_readme_branch)
                            if submodules:
                                logger.info(
                                    f'Found {len(submodules)} submodules in {time.time() - start_time:.2f} seconds'
                                )
                                details['submodules'] = [
                                    submodule.dict() for submodule in submodules
                                ]
                            else:
                                logger.info('No submodules found')

        # Process content we've gathered
        if readme_content:
            logger.info(f'Successfully extracted README content ({len(readme_content)} chars)')

            # Extract outputs from README content using Azure-specific patterns
            outputs = extract_azure_outputs_from_readme(readme_content)
            if outputs:
                logger.info(f'Extracted {len(outputs)} outputs from README')
                details['outputs'] = outputs
            else:
                logger.info('No outputs found in README')

            # Trim if too large
            if len(readme_content) > 8000:
                logger.debug(
                    f'README content exceeds 8000 characters ({len(readme_content)}), truncating...'
                )
                readme_content = readme_content[:8000] + '...\n[README truncated due to length]'
                logger.debug('README content truncated')

            details['readme_content'] = readme_content
        else:
            logger.warning('No README content found through any method')

        # Add version details if available
        if version_details:
            logger.info('Adding version details to response')
            details['version_details'] = version_details

        return details

    except Exception as e:
        logger.error(f'Error fetching Azure module details: {e}')
        logger.debug(f'Stack trace: {traceback.format_exc()}')
        return {}


async def get_azure_variables_tf(
    owner: str, repo: str, branch: str = 'main'
) -> tuple[Optional[str], Optional[List[TerraformVariable]]]:
    """Fetch and parse the variables.tf file from an Azure module GitHub repository.

    This function extends the base get_variables_tf function with Azure-specific
    variable patterns and conventions.

    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        branch: Branch name (default: main)

    Returns:
        Tuple containing the raw variables.tf content and a list of parsed TerraformVariable objects
    """
    logger.info(f'Fetching variables.tf from Azure module {owner}/{repo} ({branch} branch)')

    # Try to get the variables.tf file
    variables_url = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/variables.tf'
    logger.debug(f'Fetching variables.tf: {variables_url}')

    try:
        start_time = time.time()
        response = requests.get(variables_url, timeout=10)
        logger.debug(f'variables.tf fetch took {time.time() - start_time:.2f} seconds')

        if response.status_code == 200:
            variables_content = response.text
            logger.info(f'Found variables.tf ({len(variables_content)} chars)')

            # Parse the variables.tf file with Azure-specific patterns
            variables = parse_azure_variables_tf(variables_content)
            logger.info(f'Parsed {len(variables)} variables from variables.tf')

            return variables_content, variables
        else:
            logger.debug(
                f'No variables.tf found at {branch} branch, status: {response.status_code}'
            )
            return None, None
    except Exception as ex:
        logger.error(f'Error fetching variables.tf: {ex}')
        logger.debug(f'Stack trace: {traceback.format_exc()}')

    return None, None


def parse_azure_variables_tf(content: str) -> List[TerraformVariable]:
    """Parse variables.tf content to extract variable definitions with Azure-specific patterns.

    Args:
        content: The content of the variables.tf file

    Returns:
        List of TerraformVariable objects
    """
    if not content:
        return []

    variables = []

    # Enhanced regex pattern to match variable blocks including Azure-specific patterns
    variable_blocks = re.finditer(r'variable\s+"([^"]+)"\s*{([^}]+)}', content, re.DOTALL)

    for match in variable_blocks:
        var_name = match.group(1)
        var_block = match.group(2)

        # Initialize variable with name
        variable = TerraformVariable(name=var_name)

        # Extract type with support for Azure-specific complex types
        type_match = re.search(r'type\s*=\s*(.+?)(?=\n|$)', var_block, re.DOTALL)
        if type_match:
            var_type = type_match.group(1).strip()
            # Clean up multi-line type definitions
            var_type = re.sub(r'\s+', ' ', var_type)
            variable.type = var_type

        # Extract description
        desc_match = re.search(r'description\s*=\s*"([^"]+)"', var_block)
        if not desc_match:
            # Try multi-line description
            desc_match = re.search(r'description\s*=\s*<<-?(\w+)(.*?)\1', var_block, re.DOTALL)
            if desc_match:
                variable.description = desc_match.group(2).strip()
        else:
            variable.description = desc_match.group(1).strip()

        # Check for default value with support for Azure-specific defaults
        default_match = re.search(r'default\s*=\s*(.+?)(?=\n\s*[a-z]|\n}|$)', var_block, re.DOTALL)
        if default_match:
            default_value = default_match.group(1).strip()
            # Handle complex default values (objects, lists, etc.)
            if default_value != 'null':
                variable.default = default_value
                variable.required = False

        # Check for validation blocks (common in Azure modules)
        validation_match = re.search(r'validation\s*{([^}]+)}', var_block)
        if validation_match:
            validation_content = validation_match.group(1)
            # Extract validation condition for additional context
            condition_match = re.search(r'condition\s*=\s*(.+)', validation_content)
            if condition_match and variable.description:
                variable.description += f' (Validation: {condition_match.group(1).strip()})'

        variables.append(variable)

    return variables


def extract_azure_outputs_from_readme(readme_content: str) -> List[Dict[str, str]]:
    """Extract module outputs from Azure module README content.

    This function extends the base extract_outputs_from_readme with Azure-specific patterns.

    Args:
        readme_content: The README markdown content

    Returns:
        List of dictionaries containing output name and description
    """
    if not readme_content:
        return []

    outputs = []

    # Find the Outputs section with various Azure conventions
    lines = readme_content.split('\n')
    in_outputs_section = False
    in_outputs_table = False

    for i, line in enumerate(lines):
        # Look for Outputs heading (Azure modules often use different heading styles)
        if re.match(r'^#+\s+(Outputs?|Module\s+Outputs?|Returned\s+Values?)$', line, re.IGNORECASE):
            in_outputs_section = True
            continue

        # If we're in the outputs section, look for the table header
        if in_outputs_section and not in_outputs_table:
            if '|' in line and ('Name' in line or 'Output' in line) and ('Description' in line or 'Value' in line):
                in_outputs_table = True
                continue

        # If we're in the outputs table, parse each row
        if in_outputs_section and in_outputs_table:
            # Skip the table header separator line
            if line.strip().startswith('|') and all(c in '|-: ' for c in line):
                continue

            # If we hit another heading or the table ends, stop parsing
            if line.strip().startswith('#') or not line.strip() or '|' not in line:
                break

            # Parse the table row
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:  # Should have at least empty, name, description columns
                    name_part = parts[1].strip()
                    desc_part = parts[2].strip()

                    # Clean up any markdown formatting
                    name = re.sub(r'`(.*?)`', r'\1', name_part).strip()
                    description = re.sub(r'`(.*?)`', r'\1', desc_part).strip()

                    if name:
                        outputs.append({'name': name, 'description': description})

    # If we didn't find a table, try looking for Azure-specific list formats
    if not outputs and in_outputs_section:
        for line in lines:
            # Look for various Azure module output patterns
            list_match = re.match(r'^[-*]\s*`?([^`\s:]+)`?\s*[-:]?\s*(.+)$', line)
            if list_match:
                name = list_match.group(1).strip()
                description = list_match.group(2).strip()
                outputs.append({'name': name, 'description': description})

    logger.debug(f'Extracted {len(outputs)} outputs from Azure module README')
    return outputs


async def get_azure_module_info(module_info: Dict[str, str]) -> Optional[ModuleSearchResult]:
    """Get detailed information about a specific Azure module.

    Args:
        module_info: Dictionary with namespace, name, and provider of the module

    Returns:
        ModuleSearchResult object with module details or None if module not found
    """
    namespace = module_info['namespace']
    name = module_info['name']
    provider = module_info['provider']

    try:
        # First, check if the module exists
        details_url = f'https://registry.terraform.io/v1/modules/{namespace}/{name}/{provider}'
        response = requests.get(details_url, timeout=10)

        if response.status_code != 200:
            logger.warning(
                f'Azure module {namespace}/{name}/{provider} not found (status code: {response.status_code})'
            )
            return None

        module_data = response.json()

        # Get the description and clean it
        description = module_data.get('description', 'No description available')
        cleaned_description = clean_description(description)

        # Create the basic result
        result = ModuleSearchResult(
            name=name,
            namespace=namespace,
            provider=provider,
            version=module_data.get('latest_version', 'unknown'),
            url=f'https://registry.terraform.io/modules/{namespace}/{name}/{provider}',
            description=cleaned_description,
        )

        # Get detailed information including README
        details = await get_azure_module_details(namespace, name, provider)

        if details:
            # Update the version if we got a better one from the details
            if 'latest_version' in details:
                result.version = details['latest_version']

            # Add version details if available
            if 'version_details' in details:
                result.version_details = details['version_details']

            # Get README content
            if 'readme_content' in details and details['readme_content']:
                result.readme_content = details['readme_content']

            # Get input and output counts if available
            if 'root' in details and 'inputs' in details['root']:
                result.input_count = len(details['root']['inputs'])

            if 'root' in details and 'outputs' in details['root']:
                result.output_count = len(details['root']['outputs'])

            # Add submodules if available
            if 'submodules' in details and details['submodules']:
                submodules = [
                    SubmoduleInfo(**submodule_data) for submodule_data in details['submodules']
                ]
                result.submodules = submodules

            # Add variables information if available
            if 'variables' in details and details['variables']:
                variables = [TerraformVariable(**var_data) for var_data in details['variables']]
                result.variables = variables

            # Add variables.tf content if available
            if 'variables_content' in details and details['variables_content']:
                result.variables_content = details['variables_content']

            # Add outputs from README if available
            if 'outputs' in details and details['outputs']:
                outputs = [
                    TerraformOutput(name=output['name'], description=output.get('description'))
                    for output in details['outputs']
                ]
                result.outputs = outputs
                # Update output_count if not already set
                if result.output_count is None:
                    result.output_count = len(outputs)

        return result

    except Exception as e:
        logger.error(f'Error getting info for Azure module {namespace}/{name}/{provider}: {e}')
        return None


async def search_terraform_registry_azure_modules(query: str, limit: int = 20) -> List[ModuleSearchResult]:
    """Search the Terraform Registry for Azure modules.

    Args:
        query: Search query
        limit: Maximum number of results to return

    Returns:
        List of matching Azure modules
    """
    logger.info(f"Searching Terraform Registry for Azure modules with query: '{query}'")

    try:
        # Search the Terraform Registry for Azure modules
        search_url = 'https://registry.terraform.io/v1/modules'
        params = {
            'q': query,
            'provider': 'azurerm',
            'limit': limit,
            'offset': 0
        }

        logger.debug(f'Making search request to: {search_url} with params: {params}')
        response = requests.get(search_url, params=params, timeout=15)
        response.raise_for_status()

        search_results = response.json()
        modules = search_results.get('modules', [])

        logger.info(f'Found {len(modules)} Azure modules from registry search')

        # Process each module
        results = []
        for module_data in modules:
            try:
                # Extract basic info
                namespace = module_data.get('namespace', '')
                name = module_data.get('name', '')
                provider = module_data.get('provider', 'azurerm')
                version = module_data.get('version', 'unknown')
                description = clean_description(module_data.get('description', ''))

                # Create basic result
                result = ModuleSearchResult(
                    name=name,
                    namespace=namespace,
                    provider=provider,
                    version=version,
                    url=f'https://registry.terraform.io/modules/{namespace}/{name}/{provider}',
                    description=description,
                )

                # Add basic counts if available
                if 'root' in module_data:
                    root = module_data['root']
                    if 'inputs' in root:
                        result.input_count = len(root['inputs'])
                    if 'outputs' in root:
                        result.output_count = len(root['outputs'])

                results.append(result)

            except Exception as e:
                logger.warning(f'Error processing module data: {e}')
                continue

        return results

    except Exception as e:
        logger.error(f'Error searching Terraform Registry for Azure modules: {e}')
        return []


async def search_azure_terraform_modules_impl(
    query: str = '', 
    include_popular: bool = True,
    include_registry_search: bool = True,
    limit: int = 20
) -> List[ModuleSearchResult]:
    """Search for Azure-specific Terraform modules.

    This tool searches for Azure Terraform modules from multiple sources:
    1. Popular Azure modules (Azure namespace and community modules)
    2. Terraform Registry search results

    It returns detailed information about these modules, including their README content,
    variables.tf content, and submodules when available.

    The search is performed across module names, descriptions, README content, and variable
    definitions. This allows you to find modules based on their functionality or specific
    configuration options.

    Parameters:
        query: Search term to filter modules (empty returns popular Azure modules)
        include_popular: Whether to include popular Azure modules in results
        include_registry_search: Whether to search the Terraform Registry
        limit: Maximum number of registry search results to return

    Returns:
        A list of matching Azure modules with their details, including:
        - Basic module information (name, namespace, version)
        - Module documentation (README content)
        - Input and output parameter counts
        - Variables from variables.tf with descriptions and default values
        - Submodules information
        - Version details and release information
    """
    logger.info(f"Searching for Azure Terraform modules with query: '{query}'")

    all_results = []

    # Task 1: Get popular Azure modules if requested
    if include_popular:
        logger.info("Fetching popular Azure modules")
        popular_tasks = []
        for module_info in AZURE_POPULAR_MODULES:
            popular_tasks.append(get_azure_module_info(module_info))

        # Run popular module tasks concurrently
        popular_results = await asyncio.gather(*popular_tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        popular_modules = [
            result for result in popular_results 
            if result is not None and not isinstance(result, Exception)
        ]
        
        logger.info(f"Found {len(popular_modules)} popular Azure modules")
        all_results.extend(popular_modules)

    # Task 2: Search Terraform Registry if requested and query provided
    if include_registry_search and query.strip():
        logger.info("Searching Terraform Registry for Azure modules")
        registry_results = await search_terraform_registry_azure_modules(query, limit)
        logger.info(f"Found {len(registry_results)} modules from registry search")
        all_results.extend(registry_results)

    # Remove duplicates based on namespace/name/provider combination
    seen_modules = set()
    unique_results = []
    for result in all_results:
        module_key = f"{result.namespace}/{result.name}/{result.provider}"
        if module_key not in seen_modules:
            seen_modules.add(module_key)
            unique_results.append(result)

    # Filter results based on query if provided
    if query and query.strip():
        query_terms = query.lower().split()
        filtered_results = []

        for result in unique_results:
            # Check if any query term is in the module name, description, readme, or variables
            matches = False

            # Build search text from module details and variables
            search_text = (
                f'{result.name} {result.description} {result.readme_content or ""}'.lower()
            )

            # Add variables information to search text if available
            if result.variables:
                for var in result.variables:
                    var_text = f'{var.name} {var.type or ""} {var.description or ""}'
                    search_text += f' {var_text.lower()}'

            # Add variables.tf content to search text if available
            if result.variables_content:
                search_text += f' {result.variables_content.lower()}'

            # Add outputs information to search text if available
            if result.outputs:
                for output in result.outputs:
                    output_text = f'{output.name} {output.description or ""}'
                    search_text += f' {output_text.lower()}'

            for term in query_terms:
                if term in search_text:
                    matches = True
                    break

            if matches:
                filtered_results.append(result)

        logger.info(
            f"Found {len(filtered_results)} Azure modules matching query '{query}' out of {len(unique_results)} total modules"
        )
        return filtered_results
    else:
        logger.info(f'Returning all {len(unique_results)} Azure modules (no query filter)')
        return unique_results
