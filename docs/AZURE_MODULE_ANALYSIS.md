# Azure Terraform Module Analysis Implementation

This document describes the implementation of Azure-specific Terraform module analysis tooling that was added to accommodate Azure module conventions from the Terraform Registry and Azure marketplace.

## Overview

The implementation extends the existing module analysis system to support Azure-specific Terraform modules with specialized parsing logic for Azure module conventions, variables, outputs, and documentation patterns.

## Key Components

### 1. Azure Module Search Tool (`search_azure_terraform_modules.py`)

**Purpose**: Search, analyze, and extract comprehensive information from Azure-specific Terraform modules.

**Key Features**:
- Searches popular Azure modules from well-known namespaces (Azure, claranet, data-platform-hq, etc.)
- Integrates with Terraform Registry search for dynamic discovery
- Supports Azure marketplace URL parsing
- Handles Azure-specific variable and output patterns
- Extracts README documentation with Azure conventions

**Main Functions**:
- `search_azure_terraform_modules_impl()` - Main search interface
- `get_azure_module_info()` - Fetch detailed module information
- `search_terraform_registry_azure_modules()` - Registry search for Azure modules
- `parse_azure_variables_tf()` - Azure-specific variable parsing
- `extract_azure_outputs_from_readme()` - Azure-specific output extraction

### 2. Enhanced Utilities (`utils.py`)

**Azure-Specific Extensions**:
- `parse_azure_module_url()` - Parses Azure marketplace and DevOps URLs
- `is_azure_module()` - Detects Azure-related modules by name/description
- `get_azure_module_conventions()` - Returns Azure module patterns and conventions
- `extract_azure_outputs_from_readme()` - Azure-specific README parsing

**Azure Module Conventions Supported**:
- **Providers**: azurerm, azuread, azapi
- **Common Namespaces**: Azure, claranet, data-platform-hq, getindata, libre-devops
- **Variable Patterns**: 
  - Naming: `*_(name|prefix|suffix)`
  - Location: `.*(location|region).*`
  - Resource Group: `.*resource_group.*`
  - Tags: `.*tags?$`
  - Subscription: `.*subscription.*`
- **Output Patterns**:
  - ID: `.*_id$`
  - Name: `.*_name$`
  - Endpoint: `.*_(endpoint|url)$`
  - Connection String: `.*_connection_string$`

### 3. Enhanced User Module Search (`search_user_provided_module.py`)

**Updates**:
- Integrated Azure module URL parsing as primary method
- Falls back to standard parsing for non-Azure modules
- Supports Azure marketplace URLs and conventions

### 4. Server Integration (`server.py`)

**New Tool Added**:
- `SearchAzureTerraformModules` - MCP tool for Azure module search
- Full parameter support with documentation
- Integrated with existing tool structure

## Azure Module Conventions Supported

### Variable Patterns
The implementation recognizes Azure-specific variable patterns:
- **Location/Region variables**: Variables containing "location" or "region"
- **Resource Group variables**: Variables containing "resource_group"
- **Naming variables**: Variables ending with "_name", "_prefix", or "_suffix"
- **Tag variables**: Variables ending with "tags" or "tag"
- **Subscription variables**: Variables containing "subscription"

### Output Patterns
Azure modules typically follow these output naming conventions:
- **Resource IDs**: Outputs ending with "_id"
- **Resource Names**: Outputs ending with "_name"
- **Endpoints**: Outputs ending with "_endpoint" or "_url"
- **Connection Strings**: Outputs ending with "_connection_string"

### Validation Support
The implementation can detect and parse Azure module validation blocks:
- Location validation with allowed regions
- SKU validation with allowed values
- Complex type validation (common in Azure modules)

## URL Support

### Terraform Registry URLs
- Standard format: `namespace/name/provider`
- Registry format: `registry.terraform.io/namespace/name/provider`
- Azure providers: `azurerm`, `azuread`, `azapi`

### Azure Marketplace URLs
- Format: `https://azuremarketplace.microsoft.com/en-us/marketplace/apps/publisher.offer`
- Automatically converts to Terraform Registry format

### GitHub URLs
- Azure repositories: `https://github.com/Azure/terraform-azurerm-*`
- Community repositories with Azure indicators
- Detects provider type from repository name patterns

## Popular Azure Modules

The system includes a curated list of popular Azure modules:

### Official Azure Modules
- `Azure/aks/azurerm` - Azure Kubernetes Service
- `Azure/app-service/azurerm` - Azure App Service
- `Azure/application-gateway/azurerm` - Application Gateway
- `Azure/compute/azurerm` - Virtual Machines
- `Azure/container-registry/azurerm` - Container Registry
- `Azure/cosmosdb/azurerm` - Cosmos DB
- `Azure/database/azurerm` - Database services
- `Azure/front-door/azurerm` - Front Door CDN
- `Azure/key-vault/azurerm` - Key Vault
- `Azure/load-balancer/azurerm` - Load Balancer
- `Azure/network/azurerm` - Networking
- `Azure/storage/azurerm` - Storage Account
- `Azure/virtual-machine/azurerm` - Virtual Machines
- `Azure/vnet/azurerm` - Virtual Network

### Community Modules
- `claranet/*` - High-quality community modules
- `data-platform-hq/*` - Data platform modules
- `getindata/*` - Azure data platform solutions
- `libre-devops/*` - DevOps-focused modules

## Usage Examples

### Search for Popular Azure Modules
```python
results = await search_azure_terraform_modules_impl(
    query="",
    include_popular=True,
    include_registry_search=False
)
```

### Search for Specific Azure Modules
```python
results = await search_azure_terraform_modules_impl(
    query="aks",
    include_popular=True,
    include_registry_search=True,
    limit=10
)
```

### Parse Azure Module URLs
```python
# Terraform Registry
namespace, name, provider = parse_azure_module_url("Azure/aks/azurerm")

# Azure Marketplace
namespace, name, provider = parse_azure_module_url(
    "https://azuremarketplace.microsoft.com/en-us/marketplace/apps/microsoft.azurestack"
)

# GitHub Repository
namespace, name, provider = parse_azure_module_url(
    "https://github.com/Azure/terraform-azurerm-aks"
)
```

## Benefits

1. **Azure-Specific Parsing**: Handles Azure module conventions that differ from AWS modules
2. **Comprehensive Discovery**: Combines popular modules with dynamic registry search
3. **Marketplace Integration**: Supports Azure marketplace URLs for enterprise scenarios
4. **Rich Metadata**: Extracts variables, outputs, validation rules, and documentation
5. **Community Support**: Includes well-maintained community Azure modules
6. **Backward Compatibility**: Extends existing tooling without breaking changes

## Testing

A comprehensive test suite (`test_azure_module_analysis.py`) is included to verify:
- Azure module URL parsing
- Module detection logic
- Convention application
- Single module analysis
- Registry search functionality
- Comprehensive search scenarios

## Implementation Notes

- **Performance**: Uses async/await for concurrent module fetching
- **Caching**: Leverages existing caching mechanisms for GitHub API calls
- **Error Handling**: Robust error handling with fallback mechanisms
- **Rate Limiting**: Respects API rate limits with delays between requests
- **Documentation**: Comprehensive docstrings and examples throughout

This implementation successfully adapts the existing resource/module analysis framework to accommodate Azure-specific Terraform modules while maintaining compatibility with the existing codebase structure.
