# Azure Terraform MCP Server

MCP server for Terraform on Azure best practices, infrastructure as code patterns, and security compliance with Checkov.

## Usage

Clone the repository

## Features

- **Terraform Best Practices** - Get prescriptive Terraform advice for building applications on Azure
  - Azure Well-Architected guidance for Terraform configurations
  - Security and compliance recommendations
  - AzureRM provider prioritization for consistent API behavior

- **Security-First Development Workflow** - Follow a structured process for creating secure code
  - Step-by-step guidance for validation and security scanning
  - Integration of Checkov at the right stages of development
  - Clear handoff points between AI assistance and developer deployment

- **Checkov Integration** - Work with Checkov for security and compliance scanning
  - Run security scans on Terraform code to identify vulnerabilities
  - Automatically fix identified security issues when possible
  - Get detailed remediation guidance for compliance issues

- **Azure Provider Documentation** - Search for Azure and AzureRM provider resources
  - Find documentation for specific resources and attributes
  - Get example snippets and implementation guidance
  - Compare Azure and AzureRM provider capabilities

- **Azure Modules** - Access specialized modules for AI/ML workloads
  - Azure OpenAI module for generative AI applications
  - Azure Cognitive Search for vector search capabilities
  - Azure Machine Learning endpoint deployment for ML model hosting
  - Serverless Streamlit application deployment for AI interfaces

- **Terraform Registry Module Analysis** - Analyze Terraform Registry modules
  - Search for modules by URL or identifier
  - Extract input variables, output variables, and README content
  - Understand module usage and configuration options
  - Analyze module structure and dependencies

- **Terraform Workflow Execution** - Run Terraform commands directly
  - Initialize, plan, validate, apply, and destroy operations
  - Pass variables and specify Azure locations
  - Get formatted command output for analysis

- **Terragrunt Workflow Execution** - Run Terragrunt commands directly
  - Initialize, plan, validate, apply, run-all and destroy operations
  - Pass variables and specify Azure locations
  - Configure terragrunt-config and include/exclude paths flags
  - Get formatted command output for analysis

- **Custom Tools** - Extend functionality with custom tools
  - Execute Terraform commands with `execute_terraform_command.py`
  - Run Checkov scans with `run_checkov_scan.py`
  - Search for Azure provider documentation with `search_azure_provider_docs.py`

## Tools and Resources

- **Terraform Development Workflow**: Follow security-focused development process via `terraform://workflow_guide`
- **Azure Best Practices**: Access Azure-specific guidance via `terraform://azure_best_practices`
- **AzureAD Provider Resources**: Access resource listings via `terraform://azuread_provider_resources_listing`
- **AzureRM Provider Resources**: Access resource listings via `terraform://azurerm_provider_resources_listing`
- **AzAPI Provider Resources**: Access resource listings via `terraform://azapi_provider_resources_listing`

## Prerequisites

1. Install `uv` from [Astral](https://docs.astral.sh/uv/getting-started/installation/) or the [GitHub README](https://github.com/astral-sh/uv#installation)
2. Install Python using `uv python install 3.10`
3. Install Terraform CLI for workflow execution
4. Install Checkov for security scanning

## Installation

 `gh repoc clone Yeseh/azure-terraform-mcp && cd azure-terraform-mcp && docker build -t xebiams/terraform-mcp-server .`:

Then add the MCP configuration to your client of choice:
```json
  {
    "mcpServers": {
      "xebiams.terraform-mcp-server": {
        "command": "docker",
        "args": [
          "run",
          "--rm",
          "--interactive",
          "--env",
          "FASTMCP_LOG_LEVEL=ERROR",
          "xebiams/terraform-mcp-server:latest"
        ],
        "env": {},
        "disabled": false,
        "autoApprove": []
      }
    }
  }
```

## Security Considerations

When using this MCP server, you should consider:
- **Following the structured development workflow** that integrates validation and security scanning
- Reviewing all Checkov warnings and errors manually
- Fixing security issues rather than ignoring them whenever possible
- Documenting clear justifications for any necessary exceptions
- Using the RunCheckovScan tool regularly to verify security compliance
- Preferring the AzureRM provider for its consistent API behavior and better security defaults

Before applying Terraform changes to production environments, you should conduct your own independent assessment to ensure that your infrastructure would comply with your own specific security and quality control practices and standards, as well as the local laws, rules, and regulations that govern you and your content.
