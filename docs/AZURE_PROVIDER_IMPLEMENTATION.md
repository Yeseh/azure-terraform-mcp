# Azure Provider Documentation Implementation

This document summarizes the implementation of Azure provider documentation search tools for the Terraform MCP Server, which now supports `azurerm`, `azuread`, and `azapi` providers alongside the existing AWS providers.

## Overview

The implementation adds three new Azure provider documentation search tools that follow the same pattern as the existing AWS provider tools, but are adapted for Azure's documentation structure and endpoints.

## Implemented Azure Providers

### 1. Azure RM Provider (`azurerm`)
- **Provider**: HashiCorp's official Azure Resource Manager provider
- **GitHub Repository**: `hashicorp/terraform-provider-azurerm`
- **Documentation Base URL**: `https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs`
- **Raw Documentation URL**: `https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/main/website/docs`
- **File Structure**: 
  - Resources: `r/{resource_name}.html.markdown`
  - Data Sources: `d/{resource_name}.html.markdown`
- **Prefix**: `azurerm_`

### 2. Azure AD Provider (`azuread`)
- **Provider**: HashiCorp's official Azure Active Directory provider
- **GitHub Repository**: `hashicorp/terraform-provider-azuread`
- **Documentation Base URL**: `https://registry.terraform.io/providers/hashicorp/azuread/latest/docs`
- **Raw Documentation URL**: `https://raw.githubusercontent.com/hashicorp/terraform-provider-azuread/main/docs`
- **File Structure**: 
  - Resources: `resources/{resource_name}.md`
  - Data Sources: `data-sources/{resource_name}.md`
- **Prefix**: `azuread_`

### 3. Azure API Provider (`azapi`)
- **Provider**: Microsoft's Azure API provider for accessing Azure Resource Manager APIs
- **GitHub Repository**: `Azure/terraform-provider-azapi`
- **Documentation Base URL**: `https://registry.terraform.io/providers/Azure/azapi/latest/docs`
- **Raw Documentation URL**: `https://raw.githubusercontent.com/Azure/terraform-provider-azapi/main/docs`
- **File Structure**: 
  - Resources: `resources/{resource_name}.md`
  - Data Sources: `data-sources/{resource_name}.md`
- **Prefix**: `azapi_`

## Implementation Details

### New Model

Added `TerraformAzureProviderDocsResult` model with Azure-specific fields:
- `provider`: Identifies which Azure provider (`azurerm`, `azuread`, `azapi`)
- `arguments`: Resource arguments with descriptions
- `attributes`: Resource attributes with descriptions 
- `import_info`: Information about importing existing resources
- `timeouts`: Resource timeout configuration

### New Tools

Three new MCP tools were implemented:

1. **`SearchAzurermProviderDocs`**: Search Azure RM provider documentation
2. **`SearchAzureadProviderDocs`**: Search Azure AD provider documentation  
3. **`SearchAzapiProviderDocs`**: Search Azure API provider documentation

### URL and Endpoint Mapping

The implementation maps provider resources to GitHub documentation URLs:

| Provider | Asset Name | Asset Type | Generated URL |
|----------|------------|------------|---------------|
| azurerm | `azurerm_storage_account` | resource | `https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/main/website/docs/r/storage_account.html.markdown` |
| azurerm | `azurerm_storage_account` | data_source | `https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/main/website/docs/d/storage_account.html.markdown` |
| azuread | `azuread_user` | resource | `https://raw.githubusercontent.com/hashicorp/terraform-provider-azuread/main/docs/resources/user.md` |
| azuread | `azuread_user` | data_source | `https://raw.githubusercontent.com/hashicorp/terraform-provider-azuread/main/docs/data-sources/user.md` |
| azapi | `azapi_resource` | resource | `https://raw.githubusercontent.com/Azure/terraform-provider-azapi/main/docs/resources/resource.md` |
| azapi | `azapi_resource_list` | data_source | `https://raw.githubusercontent.com/Azure/terraform-provider-azapi/main/docs/data-sources/resource_list.md` |

### Documentation Structure Differences

The implementation handles different markdown structures across Azure providers:

1. **Azure RM**: Uses `.html.markdown` files and follows the AWS provider's structure closely
2. **Azure AD & API**: Use `.md` files with a different directory structure (`resources/` vs `r/`)

### Markdown Parsing

All Azure providers use the same markdown parser (from `search_azurerm_provider_docs`) which extracts:
- Title and description
- Example usage code blocks
- Arguments reference sections
- Attributes reference sections
- Import information
- Timeout configurations

### Prefix Handling

All tools automatically handle provider prefixes:
- `azurerm_storage_account` → `storage_account`
- `azuread_user` → `user`  
- `azapi_resource` → `resource`

Users can search with or without the prefix.

### Asset Type Support

All tools support three asset types:
- `resource`: Search only for resources
- `data_source`: Search only for data sources
- `both`: Search for both resources and data sources

## Files Modified/Created

### New Files
- `xebiams/terraform_mcp_server/impl/tools/search_azurerm_provider_docs.py`
- `xebiams/terraform_mcp_server/impl/tools/search_azuread_provider_docs.py`
- `xebiams/terraform_mcp_server/impl/tools/search_azapi_provider_docs.py`
- `test_azure_providers.py`
- `AZURE_PROVIDER_IMPLEMENTATION.md`

### Modified Files
- `xebiams/terraform_mcp_server/models/models.py`: Added `TerraformAzureProviderDocsResult` model
- `xebiams/terraform_mcp_server/models/__init__.py`: Added new model to imports
- `xebiams/terraform_mcp_server/impl/tools/__init__.py`: Added new tool implementations
- `xebiams/terraform_mcp_server/server.py`: Added new MCP tool registrations and imports

## Usage Examples

### Azure RM Provider
```python
# Search for storage account resource
results = await search_azurerm_provider_docs("azurerm_storage_account", "resource")

# Search for both resource and data source
results = await search_azurerm_provider_docs("azurerm_virtual_machine", "both")
```

### Azure AD Provider
```python
# Search for user resource
results = await search_azuread_provider_docs("azuread_user", "resource")

# Search for application data source
results = await search_azuread_provider_docs("azuread_application", "data_source")
```

### Azure API Provider
```python
# Search for generic Azure API resource
results = await search_azapi_provider_docs("azapi_resource", "resource")

# Search for resource list data source
results = await search_azapi_provider_docs("azapi_resource_list", "data_source")
```

## Testing

A comprehensive test suite verifies:
- Model instantiation and validation
- GitHub URL construction for all providers
- Prefix handling logic
- Asset type mapping

All tests pass successfully, confirming the implementation is working correctly.

## Integration with Terraform Registry

While the implementation fetches documentation from GitHub for the most up-to-date content, it maintains compatibility with Terraform Registry URLs for fallback error messages and maintains the same structure as existing AWS provider tools.

The implementation successfully extends the Terraform MCP Server to support comprehensive Azure provider documentation search alongside the existing AWS providers, providing a consistent interface for accessing provider documentation across cloud platforms.
