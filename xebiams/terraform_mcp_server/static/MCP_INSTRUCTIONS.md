# Terraform MCP Server Instructions

MCP server specialized in Azure cloud infrastructure provided through Terraform. I help you create, understand, optimize, and execute Terraform or Terragrunt configurations for Azure using security-focused development practices.

## How to Use This Server (Required Workflow)

### Step 1: Consult and Follow the Terraform Development Workflow
ALWAYS use the `terraform_development_workflow` resource to guide the development process. This workflow:

* Provides a step-by-step approach for creating valid, secure Terraform code
* Integrates validation and security scanning into the development process
* Specifies when and how to use each MCP tool
* Ensures code is properly validated before handoff to developers

### Step 2: Always ensure you're following Best Practices
ALWAYS begin by consulting the `terraform_azure_best_practices` resource which contains:

* Code base structure and organization principles
* Security best practices for Azure resources
* Backend configuration best practices
* Azure-specific implementation guidance

### Step 3: Use Provider Documentation
When implementing specific Azure resources:

* PREFER `azurerm` provider resources first (`SearchAzurermProviderDocs` tool)
* Use `azuread` provider resources (`SearchAzureadProviderDocs` tool) for Azure Active Directory needs
* Use `azapi` provider resources (`SearchAzapiProviderDocs` tool) for advanced or custom Azure resource scenarios

## Available Tools and Resources

### Core Resources
1. `terraform_development_workflow`
   * CRITICAL: Follow this guide for all Terraform development
   * Provides the structured workflow with security scanning integration
   * Outlines exactly when and how to use each MCP tool
2. `terraform_azure_best_practices`
   * REQUIRED: Reference before starting any development
   * Contains Azure-specific best practices for security and architecture
   * Guides organization and structure of Terraform projects

### Provider Resources
1. `terraform_azurerm_provider_resources_listing`
   * PREFERRED: Use `azurerm` provider resources first
   * Comprehensive listing by service category
2. `terraform_azuread_provider_resources_listing`
   * Use for Azure Active Directory-specific resources
   * Comprehensive listing by service category
3. `terraform_azapi_provider_resources_listing`
   * Use for advanced or custom Azure resource scenarios
   * Comprehensive listing by service category

### Documentation Tools

1. `SearchAzurermProviderDocs` (PREFERRED)
   * Always search `azurerm` provider resources first
   * Returns comprehensive documentation for Azure Resource Manager resources
2. `SearchAzureadProviderDocs`
   * Use for Azure Active Directory-specific resources
   * Returns comprehensive documentation for Azure AD provider resources
3. `SearchAzapiProviderDocs`
   * Use for advanced or custom Azure resource scenarios
   * Returns comprehensive documentation for `azapi` provider resources
4. `SearchUserProvidedModule`
   * Analyze any Terraform Registry module by URL or identifier
   * Extract input variables, output variables, and README content
   * Understand module usage and configuration options

### Command Execution Tools

1. `ExecuteTerraformCommand`
   * Execute Terraform commands in the sequence specified by the workflow
   * Supports: validate, init, plan, apply, destroy
2. `ExecuteTerragruntCommand`
   * Execute Terragrunt commands in the sequence specified by the workflow
   * Supports: validate, init, plan, apply, destroy, output, run-all
3. `RunCheckovScan`
   * Run after validation passes, before initialization
   * Identifies security and compliance issues

## Resource Selection Priority

1. FIRST use `azurerm` provider resources (`SearchAzurermProviderDocs` tool)
2. Use `azuread` provider resources (`SearchAzureadProviderDocs` tool) for Azure Active Directory (Microsoft Entra) needs
3. Use `azapi` provider resources (`SearchAzapiProviderDocs` tool) for advanced or custom Azure resource scenarios. This can also be used as a fallback to a missing resource in the azurerm provider.


## Examples

- "What's the best way to set up a highly available web application on Azure using Terraform?"
- "Find documentation for azurerm_virtual_machine resource"
- "Find documentation for azuread_group resource"
- "Find documentation for azapi_resource resource"
- "Execute terraform plan in my ./infrastructure directory"
- "Execute terragrunt plan in my ./infrastructure directory"
- "Execute terragrunt run-all plan in my ./infrastructure directory"
- "How can I use the azurerm provider to create a secure virtual network?"
- "Run terraform validate on my configuration and then scan for security issues."
- "Is this Azure Key Vault configuration secure? Let's scan it with Checkov."
- "Find documentation for azurerm_storage_account to ensure we're using the preferred provider."
- "Use the terraform-azurerm-modules/vnet/azure module to implement a virtual network"
- "Search for the hashicorp/azurerm/azure module and explain how to use it"
- "What variables are required for the terraform-azurerm-modules/vm/azure module?"
- "I have a multi-environment Terragrunt project. How can I run apply on all modules at once?"
- "Execute terragrunt run-all apply in my ./infrastructure directory"
- "How to construct a well-formed terragrunt hierarchy folder structure"
- "Generate common inputs for all environments using generate in Terragrunt"

## Best Practices

When interacting with this server:

1. **ALWAYS** follow the development workflow from `terraform_development_workflow`
2. **ALWAYS** consult best practices from `terraform_azure_best_practices`
3. **ALWAYS** validate and scan code before considering it ready for review
4. **ALWAYS** prefer `azurerm` provider resources when available
5. Provide **security-first** implementations by default
6. **Explain** each step of the development process to users
7. **Be specific** about your requirements and constraints
8. **Specify Azure region** when relevant to your infrastructure needs
9. **Provide context** about your architecture and use case
10. **For Terraform/Terragrunt execution**, ensure the working directory exists and contains valid Terraform/Terragrunt files
11. **Review generated code** carefully before applying changes to your infrastructure
12. When using **Terragrunt**, leverage DRY features—locals, dependencies, and generate blocks—to compose multi-env stacks.
13. **Organize repos with clear folder hierarchies** (e.g. live/, modules/) and consistent naming so both Terraform and Terragrunt code is discoverable.
