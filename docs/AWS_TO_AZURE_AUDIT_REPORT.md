# AWS to Azure Terraform MCP Server - Comprehensive Audit Report

## Executive Summary

This document provides a comprehensive audit of all AWS-specific functionality in the current Terraform MCP Server codebase and catalogs the required changes for Azure compatibility. The audit covers handlers, documentation, tool implementations, static guidance, and test cases.

## Audit Overview

### Project Structure
```
xebiams/
├── terraform_mcp_server/
│   ├── server.py                          # Main server with AWS-specific tools/resources
│   ├── impl/
│   │   ├── tools/                         # AWS-specific tool implementations
│   │   └── resources/                     # AWS provider resource listings
│   ├── models/                            # Data models (some AWS-specific)
│   ├── static/                            # AWS-specific documentation and guidance
│   └── scripts/                           # AWS provider data generation scripts
└── tests/                                 # Test cases with AWS-specific examples
```

## 1. Package and Project Structure

### 1.1 Namespace and Package Names
**Current State:**
- Package namespace: `xebiams.terraform_mcp_server`
- Project name: `xebiams.terraform-mcp-server`
- Installation command: `uvx xebiams.terraform-mcp-server@latest`

**Required Changes:**
- Rename package namespace to Azure equivalent (e.g., `azure.terraform_mcp_server`)
- Update project name in `pyproject.toml`
- Update installation references in documentation
- Consider Microsoft/Azure branding guidelines

## 2. Main Server Implementation (`server.py`)

### 2.1 Server Configuration
**Current AWS-specific elements:**
```python
# Server instructions reference AWS-specific guidance
instructions=f'{MCP_INSTRUCTIONS}'  # Contains AWS-specific workflow

# AWS-specific resources imported
from xebiams.terraform_mcp_server.static import (
    AWS_TERRAFORM_BEST_PRACTICES,
    MCP_INSTRUCTIONS,
    TERRAFORM_WORKFLOW_GUIDE,
)
```

**Required Changes:**
- Update server instructions to reference Azure best practices
- Replace AWS-specific static imports with Azure equivalents
- Update server description and metadata

### 2.2 Tool Definitions
**Current AWS-specific tools:**

1. **ExecuteTerraformCommand**
   - `aws_region` parameter (line 75)
   - Documentation mentions "AWS account" (line 78)

2. **ExecuteTerragruntCommand**
   - `aws_region` parameter (line 110)
   - Documentation mentions "AWS account" (line 123)

3. **SearchAwsProviderDocs** (lines 158-200)
   - Entire tool is AWS provider specific
   - Searches AWS provider documentation
   - Returns `TerraformAWSProviderDocsResult`

4. **SearchAwsccProviderDocs** (lines 203-251)
   - Entire tool is AWSCC provider specific
   - Searches AWSCC provider documentation
   - Returns `TerraformAWSCCProviderDocsResult`

5. **SearchSpecificAwsIaModules** (lines 254-300)
   - Searches for AWS-IA specific modules
   - Hardcoded to specific AWS modules

**Required Changes:**
- Replace `aws_region` with `azure_location`/`azure_region`
- Create `SearchAzureProviderDocs` tool
- Create `SearchAzureRmProviderDocs` tool (if supporting legacy provider)
- Create equivalent Azure module search functionality
- Update all documentation strings to reference Azure

### 2.3 Resource Definitions
**Current AWS-specific resources:**

1. **terraform_aws_provider_resources_listing** (lines 402-409)
   - Returns AWS provider resource listing
   - URI: `terraform://aws_provider_resources_listing`

2. **terraform_awscc_provider_resources_listing** (lines 412-420)
   - Returns AWSCC provider resource listing
   - URI: `terraform://awscc_provider_resources_listing`

3. **terraform_aws_best_practices** (lines 423-431)
   - Returns AWS-specific best practices
   - URI: `terraform://aws_best_practices`

**Required Changes:**
- Create `terraform_azure_provider_resources_listing`
- Create `terraform_azurerm_provider_resources_listing`
- Create `terraform_azure_best_practices`
- Update URI schemes to reflect Azure

## 3. Tool Implementations

### 3.1 AWS Provider Documentation Search (`search_aws_provider_docs.py`)
**Scope:** Complete AWS-specific implementation
- Base URLs point to AWS provider documentation (lines 45-48)
- GitHub repository: `hashicorp/terraform-provider-aws`
- Documentation parsing specific to AWS provider format
- Error messages reference AWS provider

**Required Changes:**
- Create `search_azure_provider_docs.py`
- Update base URLs to Azure provider documentation
- Change GitHub repository to `hashicorp/terraform-provider-azurerm`
- Adapt documentation parsing for Azure provider format
- Update all error messages and logging

### 3.2 AWSCC Provider Documentation Search (`search_awscc_provider_docs.py`)
**Scope:** Complete AWSCC-specific implementation
- Similar to AWS provider search but for Cloud Control API
- Base URLs point to AWSCC provider documentation
- GitHub repository: `hashicorp/terraform-provider-awscc`

**Required Changes:**
- Determine if Azure has equivalent to Cloud Control API
- Either adapt for Azure equivalent or remove if not applicable
- Consider Azure Resource Manager (ARM) provider as alternative

### 3.3 AWS-IA Modules Search (`search_specific_aws_ia_modules.py`)
**Scope:** Hardcoded AWS-specific modules
```python
SPECIFIC_MODULES = [
    {'namespace': 'aws-ia', 'name': 'bedrock', 'provider': 'aws'},
    {'namespace': 'aws-ia', 'name': 'opensearch-serverless', 'provider': 'aws'},
    {'namespace': 'aws-ia', 'name': 'sagemaker-endpoint', 'provider': 'aws'},
    {'namespace': 'aws-ia', 'name': 'serverless-streamlit-app', 'provider': 'aws'},
]
```

**Required Changes:**
- Research equivalent Azure modules
- Identify Microsoft/Azure official module namespaces
- Update module list with Azure-specific modules
- Update search logic for Azure module patterns

### 3.4 Terraform/Terragrunt Execution
**AWS-specific elements:**
- `aws_region` parameter in both implementations
- Environment variable setup for AWS regions
- AWS CLI/credential integration assumptions

**Required Changes:**
- Replace `aws_region` with Azure location parameters
- Update environment variable handling for Azure CLI
- Modify credential/authentication assumptions for Azure

### 3.5 Checkov Scan Implementation (`run_checkov_scan.py`)
**AWS-specific elements:**
- While Checkov supports multiple cloud providers, some rules are AWS-specific
- Current implementation may default to AWS-specific rule sets

**Required Changes:**
- Ensure Checkov is configured for Azure rule sets
- Update default frameworks if needed
- Verify Azure-specific security rules are included

## 4. Static Documentation and Guidance

### 4.1 AWS Best Practices (`AWS_TERRAFORM_BEST_PRACTICES.md`)
**Scope:** 2500+ lines of AWS-specific guidance
- AWS Well-Architected Framework principles
- AWS-specific security best practices
- AWS provider version management
- AWS service integration patterns
- AWS IAM and authentication patterns

**Required Changes:**
- Create `AZURE_TERRAFORM_BEST_PRACTICES.md`
- Adapt content for Azure Well-Architected Framework
- Update security practices for Azure AD/Entra ID
- Include Azure provider version management
- Cover Azure service integration patterns

### 4.2 MCP Instructions (`MCP_INSTRUCTIONS.md`)
**AWS-specific elements:**
- References to AWS-IA modules
- AWS provider preferences (AWSCC over AWS)
- AWS-specific resource selection priority
- AWS region specifications in examples

**Required Changes:**
- Update all references to Azure equivalents
- Establish Azure provider preferences
- Create Azure resource selection priorities
- Update examples with Azure regions and services

### 4.3 Provider Resource Listings
**Current files:**
- `AWS_PROVIDER_RESOURCES.md` - 1492 AWS resources and 601 data sources
- `AWSCC_PROVIDER_RESOURCES.md` - AWSCC provider resources

**Required Changes:**
- Generate `AZURE_PROVIDER_RESOURCES.md`
- Generate `AZURERM_PROVIDER_RESOURCES.md` 
- Create equivalent categorization for Azure services
- Update generation scripts for Azure providers

### 4.4 Terraform Workflow Guide (`TERRAFORM_WORKFLOW_GUIDE.md`)
**Potentially AWS-specific elements:**
- May contain AWS-specific validation steps
- AWS-specific security scanning guidance
- AWS provider configuration examples

**Required Changes:**
- Review and update for Azure-specific workflows
- Update provider configuration examples
- Ensure security scanning covers Azure best practices

## 5. Data Models (`models.py`)

### 5.1 AWS-Specific Models
```python
class TerraformAWSProviderDocsResult(TerraformProviderDocsResult):
    """AWS provider specific documentation result"""
    
class TerraformAWSCCProviderDocsResult(TerraformProviderDocsResult):
    """AWSCC provider specific documentation result"""
```

### 5.2 Request Models with AWS Parameters
```python
class TerraformExecutionRequest(BaseModel):
    aws_region: Optional[str] = Field(None, description='AWS region to use')

class TerragruntExecutionRequest(BaseModel):
    aws_region: Optional[str] = Field(None, description='AWS region to use')
```

**Required Changes:**
- Create `TerraformAzureProviderDocsResult`
- Create `TerraformAzureRmProviderDocsResult`
- Replace `aws_region` with `azure_location` or equivalent
- Update field descriptions and validation

## 6. Resource Implementation

### 6.1 AWS Provider Resource Listings
**Files:**
- `terraform_aws_provider_resources_listing.py`
- `terraform_awscc_provider_resources_listing.py`

**Required Changes:**
- Create `terraform_azure_provider_resources_listing.py`
- Create `terraform_azurerm_provider_resources_listing.py`
- Implement Azure service categorization logic

## 7. Scripts and Data Generation

### 7.1 Provider Resource Generation
**Current scripts:**
- `generate_aws_provider_resources.py`
- `generate_awscc_provider_resources.py`
- `scrape_aws_terraform_best_practices.py`

**Required Changes:**
- Create `generate_azure_provider_resources.py`
- Create `generate_azurerm_provider_resources.py`
- Create `scrape_azure_terraform_best_practices.py`
- Update scraping logic for Azure documentation sources

## 8. Test Cases

### 8.1 AWS-Specific Test Data
**Pervasive AWS references in tests:**
- AWS resource names (s3_bucket, lambda_function, etc.)
- AWS regions (us-west-2, us-east-1)
- AWS-specific provider URLs and documentation
- AWS service examples throughout test assertions

**File-by-file breakdown:**
- `test_server.py`: AWS provider tool tests, AWS resource examples
- `test_command_impl.py`: AWS region parameters in tests
- `test_execute_terraform_command.py`: AWS region parameter testing
- `test_execute_terragrunt_command.py`: AWS region parameter testing
- `test_search_user_provided_module.py`: AWS module examples
- `test_tool_implementations.py`: AWS provider documentation tests
- `test_run_checkov_scan.py`: AWS-specific security rule testing
- `conftest.py`: AWS fixture data and mock responses
- All other test files: Various AWS references

**Required Changes:**
- Update all test data to use Azure equivalents
- Replace AWS regions with Azure regions/locations
- Update resource names to Azure equivalents
- Modify mock responses for Azure provider patterns
- Update assertion logic for Azure-specific responses

### 8.2 Test Configuration
**Current configuration:**
- Mock AWS API responses
- AWS provider version expectations
- AWS-specific URL patterns

**Required Changes:**
- Create Azure API response mocks
- Update provider version expectations for Azure
- Update URL patterns for Azure documentation

## 9. Configuration and Metadata

### 9.1 Project Configuration (`pyproject.toml`)
**Current AWS-specific elements:**
```toml
name = "xebiams.terraform-mcp-server"
description = "An AWS Labs Model Context Protocol (MCP) server for terraform"
```

**Required Changes:**
- Update project name and namespace
- Update description to reflect Azure focus
- Consider Microsoft/Azure branding requirements
- Update author/maintainer information

### 9.2 Documentation (`README.md`)
**AWS-specific content:**
- Title: "AWS Terraform MCP Server"
- AWS-specific feature descriptions
- AWS provider prioritization
- AWS-IA module references
- AWS security considerations

**Required Changes:**
- Update title and all descriptions
- Replace feature descriptions with Azure equivalents
- Update provider prioritization guidance
- Reference appropriate Azure modules
- Update security considerations for Azure

## 10. Priority Matrix for Changes

### Critical (Must Change)
1. **Server tools and resources** - Core functionality
2. **Tool implementations** - All AWS provider searches
3. **Static guidance documents** - Best practices and instructions
4. **Data models** - AWS-specific fields and types
5. **Package metadata** - Names, descriptions, namespaces

### High Priority
1. **Test cases** - Ensure Azure functionality works
2. **Resource listings** - Azure provider catalogs
3. **Generation scripts** - Data pipeline for Azure resources
4. **Documentation** - README and user guides

### Medium Priority
1. **Error messages and logging** - User-facing text
2. **Example configurations** - Sample code and snippets
3. **Utility functions** - Helper methods with AWS assumptions

### Low Priority
1. **Code comments** - Internal documentation
2. **Variable names** - Internal identifiers
3. **Debug output** - Development-only content

## 11. Azure-Specific Considerations

### 11.1 Azure Provider Landscape
- **AzureRM Provider**: Primary Terraform provider for Azure
- **Azure Provider**: Legacy provider (deprecated)
- **AzureAD Provider**: For Azure Active Directory resources
- **AzAPI Provider**: For Azure REST API resources not in AzureRM

### 11.2 Azure Service Mappings
Common AWS to Azure service mappings needed:
- S3 → Blob Storage
- Lambda → Azure Functions
- RDS → Azure SQL Database
- EKS → AKS
- Route53 → DNS Zones
- CloudWatch → Azure Monitor
- IAM → Azure RBAC/Entra ID

### 11.3 Azure Regions vs AWS Regions
- Azure uses different region naming conventions
- Azure has region pairs for disaster recovery
- Different availability zone concepts

### 11.4 Azure Well-Architected Framework
- Security pillar
- Reliability pillar  
- Performance efficiency pillar
- Cost optimization pillar
- Operational excellence pillar

## 12. Recommended Implementation Strategy

### Phase 1: Core Infrastructure
1. Update package structure and namespaces
2. Modify server.py tool and resource definitions
3. Create Azure provider documentation search tools
4. Update core data models

### Phase 2: Content Migration
1. Create Azure best practices documentation
2. Generate Azure provider resource listings
3. Update MCP instructions for Azure
4. Create Azure-specific module search

### Phase 3: Testing and Validation
1. Update all test cases for Azure
2. Create Azure-specific test fixtures
3. Validate Azure provider integration
4. Test end-to-end workflows

### Phase 4: Documentation and Polish
1. Update README and user documentation
2. Create Azure-specific examples
3. Update error messages and user-facing text
4. Final testing and quality assurance

## 13. Estimated Effort

### File Change Summary
- **Complete rewrite**: 8 files (tool implementations, static docs)
- **Major modifications**: 15 files (server, models, tests)
- **Minor updates**: 25+ files (documentation, examples, config)
- **New files needed**: 10+ files (Azure equivalents)

### Lines of Code Impact
- **AWS Best Practices**: 2,500+ lines to adapt
- **Tool implementations**: 1,500+ lines to rewrite
- **Test cases**: 2,000+ lines to update
- **Resource listings**: Generated content, scripts need updating
- **Total estimated**: 8,000+ lines of code changes

This audit provides a comprehensive roadmap for transforming the AWS-focused Terraform MCP Server into an Azure-compatible version. Each section identified requires careful consideration of Azure-specific patterns, services, and best practices to ensure feature parity and optimal user experience.
