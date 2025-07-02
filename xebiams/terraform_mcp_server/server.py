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

#!/usr/bin/env python3
"""terraform MCP server implementation."""

from xebiams.terraform_mcp_server.impl.resources import (
    terraform_azapi_provider_assets_listing_impl,
    terraform_azuread_provider_assets_listing_impl,
    terraform_azurerm_provider_assets_listing_impl,
)
from xebiams.terraform_mcp_server.impl.tools import (
    search_azurerm_provider_docs_impl,
    search_azuread_provider_docs_impl,
    search_azapi_provider_docs_impl,
)
from xebiams.terraform_mcp_server.impl.tools.execute_terraform_command import execute_terraform_command_impl
from xebiams.terraform_mcp_server.impl.tools.run_checkov_scan import run_checkov_scan_impl
from xebiams.terraform_mcp_server.impl.tools.search_azure_terraform_modules import search_azure_terraform_modules_impl
from xebiams.terraform_mcp_server.impl.tools.search_user_provided_module import search_user_provided_module_impl
from xebiams.terraform_mcp_server.models import (
    TerraformAzureProviderDocsResult,
)
from xebiams.terraform_mcp_server.models.models import CheckovScanRequest, CheckovScanResult, ModuleSearchResult, SearchUserProvidedModuleRequest, SearchUserProvidedModuleResult, TerraformExecutionRequest, TerraformExecutionResult, TerragruntExecutionRequest, TerragruntExecutionResult
from xebiams.terraform_mcp_server.static import (
   MCP_INSTRUCTIONS,
   AZURE_TERRAFORM_BEST_PRACTICES,
   TERRAFORM_WORKFLOW_GUIDE
)
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Any, Dict, List, Literal, Optional


mcp = FastMCP(
    'terraform_mcp_server',
    instructions=f'{MCP_INSTRUCTIONS}',
    dependencies=[
        'pydantic',
        'loguru',
        'requests',
        'beautifulsoup4',
        'PyPDF2',
    ],
)


# * Tools
@mcp.tool(name='ExecuteTerraformCommand')
async def execute_terraform_command(
    command: Literal['init', 'plan', 'validate', 'apply', 'destroy'] = Field(
        ..., description='Terraform command to execute'
    ),
    working_directory: str = Field(..., description='Directory containing Terraform files'),
    variables: Optional[Dict[str, str]] = Field(None, description='Terraform variables to pass'),
    aws_region: Optional[str] = Field(None, description='AWS region to use'),
    strip_ansi: bool = Field(True, description='Whether to strip ANSI color codes from output'),
) -> TerraformExecutionResult:
    """Execute Terraform workflow commands against an AWS account.

    This tool runs Terraform commands (init, plan, validate, apply, destroy) in the
    specified working directory, with optional variables and region settings.

    Parameters:
        command: Terraform command to execute
        working_directory: Directory containing Terraform files
        variables: Terraform variables to pass
        aws_region: AWS region to use
        strip_ansi: Whether to strip ANSI color codes from output

    Returns:
        A TerraformExecutionResult object containing command output and status
    """
    request = TerraformExecutionRequest(
        command=command,
        working_directory=working_directory,
        variables=variables,
        aws_region=aws_region,
        strip_ansi=strip_ansi,
    )
    return await execute_terraform_command_impl(request)

@mcp.tool(name='RunCheckovScan')
async def run_checkov_scan(
    working_directory: str = Field(..., description='Directory containing Terraform files'),
    framework: str = Field(
        'terraform', description='Framework to scan (terraform, arm, bicep, cloudformation, etc.)'
    ),
    check_ids: Optional[List[str]] = Field(None, description='Specific check IDs to run'),
    skip_check_ids: Optional[List[str]] = Field(None, description='Check IDs to skip'),
    output_format: str = Field('json', description='Output format (json, cli, etc.)'),
) -> CheckovScanResult:
    """Run Azure-focused Checkov security scan on Terraform code.

    This tool runs Checkov to scan Terraform code for Azure security and compliance issues,
    automatically detecting compliance frameworks and applying appropriate checks including:
    - Azure CIS Benchmark controls
    - Microsoft Cloud Security Benchmark
    - Azure Security Framework requirements
    - Azure Well-Architected Framework security pillar

    The tool automatically detects Azure compliance mode based on your infrastructure
    and applies relevant security policies. It provides Azure-specific remediation
    guidance for identified vulnerabilities.

    Supported Azure Frameworks:
    - terraform: Azure Terraform (azurerm, azuread, azapi providers)
    - arm: Azure Resource Manager templates
    - bicep: Azure Bicep files

    Azure Security Controls Covered:
    - Identity and Access Management (Azure AD, MFA, RBAC)
    - Storage Account security (encryption, network access)
    - Virtual Machine security (disk encryption, NSG rules)
    - Key Vault security (network restrictions, soft delete)
    - Database security (TDE, auditing, threat detection)
    - Network security (DDoS protection, WAF, Network Watcher)
    - Security Center configuration and monitoring

    Parameters:
        working_directory: Directory containing Terraform files to scan
        framework: Framework to scan (default: terraform, supports arm, bicep)
        check_ids: Optional list of specific check IDs to run (auto-detected if not provided)
        skip_check_ids: Optional list of check IDs to skip
        output_format: Format for scan results (default: json)

    Returns:
        A CheckovScanResult object containing scan results, identified vulnerabilities,
        and Azure-specific remediation guidance
    """
    request = CheckovScanRequest(
        working_directory=working_directory,
        framework=framework,
        check_ids=check_ids,
        skip_check_ids=skip_check_ids,
        output_format=output_format,
    )
    return await run_checkov_scan_impl(request)


@mcp.tool(name='SearchUserProvidedModule')
async def search_user_provided_module(
    module_url: str = Field(
        ..., description='URL or identifier of the Terraform module (e.g., "hashicorp/consul/aws")'
    ),
    version: Optional[str] = Field(None, description='Specific version of the module to analyze'),
    variables: Optional[Dict[str, Any]] = Field(
        None, description='Variables to use when analyzing the module'
    ),
) -> SearchUserProvidedModuleResult:
    """Search for a user-provided Terraform registry module and understand its inputs, outputs, and usage.

    This tool takes a Terraform registry module URL and analyzes its input variables,
    output variables, README, and other details to provide comprehensive information
    about the module.

    The module URL should be in the format "namespace/name/provider" (e.g., "hashicorp/consul/aws")
    or "registry.terraform.io/namespace/name/provider".

    Examples:
        - To search for the HashiCorp Consul module:
          search_user_provided_module(module_url='hashicorp/consul/aws')

        - To search for a specific version of a module:
          search_user_provided_module(module_url='terraform-aws-modules/vpc/aws', version='3.14.0')

        - To search for a module with specific variables:
          search_user_provided_module(
              module_url='terraform-aws-modules/eks/aws',
              variables={'cluster_name': 'my-cluster', 'vpc_id': 'vpc-12345'}
          )

    Parameters:
        module_url: URL or identifier of the Terraform module (e.g., "hashicorp/consul/aws")
        version: Optional specific version of the module to analyze
        variables: Optional dictionary of variables to use when analyzing the module

    Returns:
        A SearchUserProvidedModuleResult object containing module information
    """
    request = SearchUserProvidedModuleRequest(
        module_url=module_url,
        version=version,
        variables=variables,
    )
    return await search_user_provided_module_impl(request)


@mcp.tool(name='SearchAzureTerraformModules')
async def search_azure_terraform_modules(
    query: str = Field(
        '', description='Search term to filter modules (empty returns popular Azure modules)'
    ),
    include_popular: bool = Field(
        True, description='Whether to include popular Azure modules in results'
    ),
    include_registry_search: bool = Field(
        True, description='Whether to search the Terraform Registry'
    ),
    limit: int = Field(
        20, description='Maximum number of registry search results to return'
    ),
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

    Examples:
        - To get popular Azure modules:
          search_azure_terraform_modules()

        - To find modules related to AKS:
          search_azure_terraform_modules(query='aks')

        - To find modules related to storage:
          search_azure_terraform_modules(query='storage')

        - To search only the registry (not popular modules):
          search_azure_terraform_modules(query='networking', include_popular=False)

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
    return await search_azure_terraform_modules_impl(
        query=query,
        include_popular=include_popular,
        include_registry_search=include_registry_search,
        limit=limit
    )


# * Resources
@mcp.resource(
    name='terraform_development_workflow',
    uri='terraform://development_workflow',
    description='Terraform Development Workflow Guide with integrated validation and security scanning',
    mime_type='text/markdown',
)
async def terraform_development_workflow() -> str:
    """Provides guidance for developing Terraform code and integrates with Terraform workflow commands."""
    return f'{TERRAFORM_WORKFLOW_GUIDE}'


@mcp.resource(
    name='terraform_azurerm_provider_resources_listing',
    uri='terraform://azurerm_provider_resources_listing',
    description='Comprehensive listing of AzureRM provider resources and data sources by service category',
    mime_type='text/markdown',
)
async def terraform_azurerm_provider_resources_listing() -> str:
    """Provides an up-to-date categorized listing of all AzureRM provider resources and data sources."""
    return await terraform_azurerm_provider_assets_listing_impl()


@mcp.resource(
    name='terraform_azuread_provider_resources_listing',
    uri='terraform://azuread_provider_resources_listing',
    description='Comprehensive listing of AzureAD provider resources and data sources by service category',
    mime_type='text/markdown',
)
async def terraform_azuread_provider_resources_listing() -> str:
    """Provides an up-to-date categorized listing of all AzureAD provider resources and data sources."""
    return await terraform_azuread_provider_assets_listing_impl()


@mcp.resource(
    name='terraform_azapi_provider_resources_listing',
    uri='terraform://azapi_provider_resources_listing',
    description='Comprehensive listing of AzAPI provider resources and data sources by service category',
    mime_type='text/markdown',
)
async def terraform_azapi_provider_resources_listing() -> str:
    """Provides an up-to-date categorized listing of all AzAPI provider resources and data sources."""
    return await terraform_azapi_provider_assets_listing_impl()

@mcp.tool(name='SearchAzurermProviderDocs')
async def search_azurerm_provider_docs(
    asset_name: str = Field(...,
                           description='Name of the Azure RM Provider resource or data source (e.g., azurerm_storage_account)'),
    asset_type: str = Field('resource',
                            description="Type of documentation to search - 'resource' (default), 'data_source', or 'both'"),
) -> List[TerraformAzureProviderDocsResult]:
    """Search Azure RM provider documentation for resources and data sources.

    This tool searches the Terraform Azure RM provider documentation for information about
    specific assets, which can either be resources or data sources. It retrieves comprehensive details including
    descriptions, example code snippets, argument references, and attribute references.

    The implementation fetches documentation directly from the official Terraform Azure RM provider
    GitHub repository to ensure the most up-to-date information. Results are cached for
    improved performance on subsequent queries.

    Use the 'asset_type' parameter to specify if you are looking for information about provider
    resources, data sources, or both. The tool will automatically handle prefixes - you can
    search for either 'azurerm_storage_account' or 'storage_account'.

    Examples:
        - To get documentation for a storage account resource:
          search_azurerm_provider_docs(asset_name='azurerm_storage_account')

        - To search only for data sources:
          search_azurerm_provider_docs(asset_name='azurerm_storage_account', asset_type='data_source')

        - To search only for resources:
          search_azurerm_provider_docs(asset_name='azurerm_virtual_machine', asset_type='resource')

    Parameters:
        asset_name: Name of the Azure RM Provider resource or data source to look for (e.g., 'azurerm_storage_account', 'azurerm_virtual_machine')
        asset_type: Type of documentation to search - 'resource' (default), 'data_source', or 'both'. Some resources and data sources share the same name.

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
    return await search_azurerm_provider_docs_impl(asset_name, asset_type)

@mcp.tool(name='SearchAzureadProviderDocs')
async def search_azuread_provider_docs(
    asset_name: str = Field(...,
                           description='Name of the Azure AD Provider resource or data source (e.g., azuread_user)'),
    asset_type: str = Field('resource',
                            description="Type of documentation to search - 'resource' (default), 'data_source', or 'both'"),
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
          search_azuread_provider_docs(asset_name='azuread_user')

        - To search only for data sources:
          search_azuread_provider_docs(asset_name='azuread_user', asset_type='data_source')

        - To search only for resources:
          search_azuread_provider_docs(asset_name='azuread_application', asset_type='resource')

    Parameters:
        asset_name: Name of the Azure AD Provider resource or data source to look for (e.g., 'azuread_user', 'azuread_application')
        asset_type: Type of documentation to search - 'resource' (default), 'data_source', or 'both'. Some resources and data sources share the same name.

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
    return await search_azuread_provider_docs_impl(asset_name, asset_type)

@mcp.tool(name='SearchAzapiProviderDocs')
async def search_azapi_provider_docs(
    asset_name: str = Field(...,
                           description='Name of the Azure API Provider resource or data source (e.g., azapi_resource)'),
    asset_type: str = Field('resource',
                            description="Type of documentation to search - 'resource' (default), 'data_source', or 'both'"),
) -> List[TerraformAzureProviderDocsResult]:
    """Search Azure API provider documentation for resources and data sources.

    This tool searches the Terraform Azure API provider documentation for information about
    specific assets, which can either be resources or data sources. It retrieves comprehensive details including
    descriptions, example code snippets, argument references, and attribute references.

    The Azure API provider provides a generic interface to Azure Resource Manager APIs that are not
    yet covered by the Azure RM provider, allowing access to preview and experimental features.

    The implementation fetches documentation directly from the official Terraform Azure API provider
    GitHub repository to ensure the most up-to-date information. Results are cached for
    improved performance on subsequent queries.

    Use the 'asset_type' parameter to specify if you are looking for information about provider
    resources, data sources, or both. The tool will automatically handle prefixes - you can
    search for either 'azapi_resource' or 'resource'.

    Examples:
        - To get documentation for an azapi resource:
          search_azapi_provider_docs(asset_name='azapi_resource')

        - To search only for data sources:
          search_azapi_provider_docs(asset_name='azapi_resource_list', asset_type='data_source')

        - To search only for resources:
          search_azapi_provider_docs(asset_name='azapi_update_resource', asset_type='resource')

    Parameters:
        asset_name: Name of the Azure API Provider resource or data source to look for (e.g., 'azapi_resource', 'azapi_update_resource')
        asset_type: Type of documentation to search - 'resource' (default), 'data_source', or 'both'. Some resources and data sources share the same name.

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
    return await search_azapi_provider_docs_impl(asset_name, asset_type)

@mcp.resource(
    name='terraform_aws_best_practices',
    uri='terraform://aws_best_practices',
    description='AWS Terraform Provider Best Practices from AWS Prescriptive Guidance',
    mime_type='text/markdown',
)
async def terraform_aws_best_practices() -> str:
    """Provides AWS Terraform Provider Best Practices guidance."""
    return f'{AZURE_TERRAFORM_BEST_PRACTICES}'


def main():
    """Run the MCP server with CLI argument support."""
    mcp.run()


if __name__ == '__main__':
    main()
