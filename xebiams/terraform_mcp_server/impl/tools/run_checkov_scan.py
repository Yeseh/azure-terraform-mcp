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

"""Implementation of Checkov scan tools."""

import json
import os
import re
import subprocess
from xebiams.terraform_mcp_server.impl.tools.utils import get_dangerous_patterns
from xebiams.terraform_mcp_server.models import (
    CheckovScanRequest,
    CheckovScanResult,
    CheckovVulnerability,
)
from loguru import logger
from typing import Any, Dict, List, Tuple


def _clean_output_text(text: str) -> str:
    """Clean output text by removing or replacing problematic Unicode characters.

    Args:
        text: The text to clean

    Returns:
        Cleaned text with ASCII-friendly replacements
    """
    if not text:
        return text

    # First remove ANSI escape sequences (color codes, cursor movement)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)

    # Remove C0 and C1 control characters (except common whitespace)
    control_chars = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]')
    text = control_chars.sub('', text)

    # Replace HTML entities
    html_entities = {
        '-&gt;': '->',  # Replace HTML arrow
        '&lt;': '<',  # Less than
        '&gt;': '>',  # Greater than
        '&amp;': '&',  # Ampersand
    }
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)

    # Replace box-drawing and other special Unicode characters with ASCII equivalents
    unicode_chars = {
        '\u2500': '-',  # Horizontal line
        '\u2502': '|',  # Vertical line
        '\u2514': '+',  # Up and right
        '\u2518': '+',  # Up and left
        '\u2551': '|',  # Double vertical
        '\u2550': '-',  # Double horizontal
        '\u2554': '+',  # Double down and right
        '\u2557': '+',  # Double down and left
        '\u255a': '+',  # Double up and right
        '\u255d': '+',  # Double up and left
        '\u256c': '+',  # Double cross
        '\u2588': '#',  # Full block
        '\u25cf': '*',  # Black circle
        '\u2574': '-',  # Left box drawing
        '\u2576': '-',  # Right box drawing
        '\u2577': '|',  # Down box drawing
        '\u2575': '|',  # Up box drawing
    }
    for char, replacement in unicode_chars.items():
        text = text.replace(char, replacement)

    return text


def _get_azure_cis_checks() -> List[str]:
    """Get list of Azure CIS benchmark check IDs.
    
    Returns:
        List of Azure CIS check IDs for compliance scanning
    """
    return [
        # Identity and Access Management
        'CKV_AZURE_1',   # MFA enabled for all users
        'CKV_AZURE_2',   # Password policy configured
        'CKV_AZURE_3',   # Guest user access reviewed
        'CKV_AZURE_4',   # Admin accounts have MFA
        'CKV_AZURE_5',   # Service principals configured
        
        # Security Center
        'CKV_AZURE_19',  # Security Center Standard tier enabled
        'CKV_AZURE_20',  # Security Center email notifications
        'CKV_AZURE_21',  # Security Center auto-provisioning
        'CKV_AZURE_22',  # Security Center contact details
        
        # Storage Security
        'CKV_AZURE_33',  # Storage account encryption enabled
        'CKV_AZURE_34',  # Storage account secure transfer
        'CKV_AZURE_35',  # Storage account network access restricted
        'CKV_AZURE_36',  # Storage account logging enabled
        'CKV_AZURE_37',  # Storage account activity logs
        'CKV_AZURE_59',  # Storage account public access disabled
        
        # VM Security
        'CKV_AZURE_50',  # VM disk encryption enabled
        'CKV_AZURE_51',  # VM extensions secured
        'CKV_AZURE_52',  # VM managed disks used
        'CKV_AZURE_77',  # NSG rules configured properly
        'CKV_AZURE_78',  # VM backup configured
        
        # Key Vault Security
        'CKV_AZURE_109', # Key Vault network access restricted
        'CKV_AZURE_110', # Key Vault soft delete enabled
        'CKV_AZURE_111', # Key Vault purge protection enabled
        'CKV_AZURE_112', # Key Vault keys have expiration
        'CKV_AZURE_113', # Key Vault secrets have expiration
        'CKV_AZURE_114', # Key Vault logging enabled
        
        # Network Security
        'CKV_AZURE_54',  # Network Watcher enabled
        'CKV_AZURE_94',  # DDoS protection enabled
        'CKV_AZURE_122', # Application Gateway WAF enabled
        'CKV_AZURE_123', # Network security groups configured
        
        # Database Security
        'CKV_AZURE_23',  # SQL database encryption enabled
        'CKV_AZURE_24',  # SQL server auditing enabled
        'CKV_AZURE_25',  # SQL server threat detection enabled
        'CKV_AZURE_26',  # SQL server firewall configured
        'CKV_AZURE_27',  # SQL server Azure AD integration
    ]


def _get_azure_security_framework_checks() -> List[str]:
    """Get list of Azure Security Framework check IDs.
    
    Returns:
        List of Azure Security Framework check IDs
    """
    return [
        # Data Protection
        'CKV_AZURE_190', # Data classification enabled
        'CKV_AZURE_191', # Information protection policies
        'CKV_AZURE_192', # Data loss prevention
        
        # Identity Management
        'CKV_AZURE_193', # Zero trust implementation
        'CKV_AZURE_194', # Conditional access policies
        'CKV_AZURE_195', # Privileged access management
        
        # Asset Management
        'CKV_AZURE_196', # Resource inventory maintained
        'CKV_AZURE_197', # Resource tagging implemented
        'CKV_AZURE_198', # Resource governance enabled
        
        # Logging and Monitoring
        'CKV_AZURE_199', # Azure Monitor enabled
        'CKV_AZURE_200', # Azure Sentinel configured
        'CKV_AZURE_201', # Security event monitoring
    ]


def _get_microsoft_cloud_benchmark_checks() -> List[str]:
    """Get list of Microsoft Cloud Security Benchmark check IDs.
    
    Returns:
        List of Microsoft Cloud Security Benchmark check IDs
    """
    return [
        # Governance and Compliance
        'CKV_AZURE_210', # Azure Policy assignments
        'CKV_AZURE_211', # Compliance monitoring
        'CKV_AZURE_212', # Regulatory compliance
        
        # Incident Response
        'CKV_AZURE_213', # Incident response procedures
        'CKV_AZURE_214', # Automated responses
        'CKV_AZURE_215', # Security playbooks
        
        # Business Continuity
        'CKV_AZURE_216', # Backup strategies
        'CKV_AZURE_217', # Disaster recovery
        'CKV_AZURE_218', # Recovery testing
    ]


def _detect_azure_compliance_mode(working_dir: str) -> str:
    """Detect the Azure compliance mode based on files in the working directory.
    
    Args:
        working_dir: The directory containing Terraform files
        
    Returns:
        String indicating the compliance mode: 'cis', 'security_framework', 'microsoft_benchmark', or 'comprehensive'
    """
    try:
        # Look for compliance indicator files
        compliance_files = [
            'cis.tf', 'cis-compliance.tf', 'azure-cis.tf',
            'security-framework.tf', 'azure-security.tf',
            'microsoft-benchmark.tf', 'cloud-benchmark.tf',
            'compliance.tf'
        ]
        
        # Check for .checkov configuration files
        checkov_config_files = [
            '.checkov.yaml', '.checkov.yml',
            'checkov.yaml', 'checkov.yml',
            'azure-cis-checkov.yaml', 'azure-security-checkov.yaml'
        ]
        
        # Scan directory for Terraform files and check content
        for root, dirs, files in os.walk(working_dir):
            for file in files:
                if file.endswith('.tf'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            
                            # Check for CIS-specific patterns
                            if any(pattern in content for pattern in [
                                'cis benchmark', 'cis compliance', 'cis controls',
                                'center for internet security', 'ckv_azure_1',
                                'security_center_subscription_pricing'
                            ]):
                                return 'cis'
                            
                            # Check for Security Framework patterns
                            elif any(pattern in content for pattern in [
                                'azure security framework', 'security baseline',
                                'azure_policy_assignment', 'security monitoring'
                            ]):
                                return 'security_framework'
                            
                            # Check for Microsoft Cloud Benchmark patterns
                            elif any(pattern in content for pattern in [
                                'microsoft cloud security benchmark',
                                'azure defender', 'microsoft defender',
                                'azure sentinel'
                            ]):
                                return 'microsoft_benchmark'
                                
                    except (UnicodeDecodeError, PermissionError):
                        # Skip files that can't be read
                        continue
                
                # Check for specific compliance configuration files
                if file in compliance_files:
                    if 'cis' in file:
                        return 'cis'
                    elif 'security' in file or 'framework' in file:
                        return 'security_framework'
                    elif 'microsoft' in file or 'benchmark' in file:
                        return 'microsoft_benchmark'
                        
                # Check for Checkov configuration files
                if file in checkov_config_files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            config_content = f.read().lower()
                            if 'cis' in config_content:
                                return 'cis'
                            elif 'security framework' in config_content:
                                return 'security_framework'
                            elif 'microsoft' in config_content:
                                return 'microsoft_benchmark'
                    except (UnicodeDecodeError, PermissionError):
                        continue
        
        # Default to comprehensive if no specific mode detected
        return 'comprehensive'
        
    except Exception as e:
        logger.warning(f'Error detecting Azure compliance mode: {e}')
        return 'comprehensive'


def _get_azure_remediation_guidance(vulnerability: CheckovVulnerability) -> str:
    """Get Azure-specific remediation guidance for a vulnerability.
    
    Args:
        vulnerability: The CheckovVulnerability object
        
    Returns:
        String containing remediation guidance
    """
    remediation_map = {
        # Storage Security
        'CKV_AZURE_33': """
Remediation: Enable secure transfer for Azure Storage Account
1. Add 'enable_https_traffic_only = true' to your azurerm_storage_account resource
2. Set 'min_tls_version = "TLS1_2"' for enhanced security
3. Verify all applications use HTTPS endpoints

Example:
resource "azurerm_storage_account" "example" {
  enable_https_traffic_only = true
  min_tls_version          = "TLS1_2"
}
""",
        
        'CKV_AZURE_35': """
Remediation: Restrict Storage Account network access
1. Configure network_rules block in azurerm_storage_account
2. Set default_action = "Deny"
3. Add allowed IP ranges and virtual networks
4. Use private endpoints for secure access

Example:
resource "azurerm_storage_account" "example" {
  network_rules {
    default_action = "Deny"
    ip_rules       = ["10.0.0.0/16"]
  }
}
""",
        
        # VM Security
        'CKV_AZURE_50': """
Remediation: Enable VM disk encryption
1. Create azurerm_disk_encryption_set resource
2. Reference it in your VM's os_disk configuration
3. Enable encryption_at_host_enabled for additional security

Example:
resource "azurerm_linux_virtual_machine" "example" {
  encryption_at_host_enabled = true
  os_disk {
    disk_encryption_set_id = azurerm_disk_encryption_set.example.id
  }
}
""",
        
        # Key Vault Security
        'CKV_AZURE_109': """
Remediation: Restrict Key Vault network access
1. Set public_network_access_enabled = false
2. Configure network_acls with default_action = "Deny"
3. Use private endpoints for secure access

Example:
resource "azurerm_key_vault" "example" {
  public_network_access_enabled = false
  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
  }
}
""",
        
        'CKV_AZURE_110': """
Remediation: Enable Key Vault soft delete
1. Set soft_delete_retention_days = 90 (or desired value)
2. Ensure purge_protection_enabled = true for production

Example:
resource "azurerm_key_vault" "example" {
  soft_delete_retention_days = 90
  purge_protection_enabled   = true
}
""",
        
        # Database Security
        'CKV_AZURE_23': """
Remediation: Enable SQL Database encryption
1. Set transparent_data_encryption_enabled = true
2. Configure threat_detection_policy
3. Enable auditing and monitoring

Example:
resource "azurerm_mssql_database" "example" {
  transparent_data_encryption_enabled = true
  threat_detection_policy {
    state = "Enabled"
  }
}
""",
        
        # Security Center
        'CKV_AZURE_19': """
Remediation: Enable Security Center Standard tier
1. Create azurerm_security_center_subscription_pricing resources
2. Set tier = "Standard" for all resource types
3. Configure security contacts and notifications

Example:
resource "azurerm_security_center_subscription_pricing" "vm" {
  tier          = "Standard"
  resource_type = "VirtualMachines"
}
""",
    }
    
    return remediation_map.get(vulnerability.id, 
        f"No specific remediation guidance available for {vulnerability.id}. "
        f"Please refer to Azure Security documentation and CIS benchmarks.")


def _ensure_checkov_installed() -> bool:
    """Ensure Checkov is installed with Azure provider support, and install it if not.

    Returns:
        True if Checkov is installed or was successfully installed, False otherwise
    """
    try:
        # Check if Checkov is already installed
        result = subprocess.run(
            ['checkov', '--version'],
            capture_output=True,
            text=True,
            check=False,
        )
        logger.info(f'Checkov is already installed: {result.stdout.strip()}')
        
        # Check if Azure provider is available
        result = subprocess.run(
            ['checkov', '--list', '--framework', 'terraform'],
            capture_output=True,
            text=True,
            check=False,
        )
        if 'AZURE' in result.stdout or 'azurerm' in result.stdout:
            logger.info('Azure provider support detected in Checkov')
        else:
            logger.warning('Azure provider support may not be fully available')
        
        return True
    except FileNotFoundError:
        logger.warning('Checkov not found, attempting to install with Azure support')
        try:
            # Install Checkov using pip
            subprocess.run(
                ['pip', 'install', 'checkov[azure]'],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info('Successfully installed Checkov with Azure support')
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f'Failed to install Checkov: {e}')
            try:
                # Fallback to basic installation
                subprocess.run(
                    ['pip', 'install', 'checkov'],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                logger.info('Successfully installed basic Checkov')
                return True
            except subprocess.CalledProcessError as e2:
                logger.error(f'Failed to install basic Checkov: {e2}')
                return False


def _parse_checkov_json_output(output: str) -> Tuple[List[CheckovVulnerability], Dict[str, Any]]:
    """Parse Checkov JSON output into structured vulnerability data.

    Args:
        output: JSON output from Checkov scan

    Returns:
        Tuple of (list of vulnerabilities, summary dictionary)
    """
    try:
        data = json.loads(output)
        vulnerabilities = []
        summary = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'parsing_errors': 0,
            'resource_count': 0,
        }

        # Extract summary information
        if 'summary' in data:
            summary = data['summary']

        # Process check results
        if 'results' in data and 'failed_checks' in data['results']:
            for check in data['results']['failed_checks']:
                vuln = CheckovVulnerability(
                    id=check.get('check_id', 'UNKNOWN'),
                    type=check.get('check_type', 'terraform'),
                    resource=check.get('resource', 'UNKNOWN'),
                    file_path=check.get('file_path', 'UNKNOWN'),
                    line=check.get('file_line_range', [0, 0])[0],
                    description=check.get('check_name', 'UNKNOWN'),
                    guideline=check.get('guideline', None),
                    severity=(check.get('severity', 'MEDIUM') or 'MEDIUM').upper(),
                    fixed=False,
                    fix_details=None,
                )
                vulnerabilities.append(vuln)

        return vulnerabilities, summary
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse Checkov JSON output: {e}')
        return [], {'error': 'Failed to parse JSON output'}


async def run_checkov_scan_impl(request: CheckovScanRequest) -> CheckovScanResult:
    """Run Checkov scan on Terraform code with Azure-specific security policies.

    Args:
        request: Details about the Checkov scan to execute

    Returns:
        A CheckovScanResult object containing scan results and vulnerabilities
    """
    logger.info(f'Running Azure-focused Checkov scan in {request.working_directory}')

    # Ensure Checkov is installed
    if not _ensure_checkov_installed():
        return CheckovScanResult(
            status='error',
            working_directory=request.working_directory,
            error_message='Failed to install Checkov. Please install it manually with: pip install checkov',
            vulnerabilities=[],
            summary={},
            raw_output=None,
        )

    # Security checks for parameters

    # Check framework parameter for allowed values - expanded for Azure
    allowed_frameworks = ['terraform', 'cloudformation', 'kubernetes', 'dockerfile', 'arm', 'bicep', 'all']
    if request.framework not in allowed_frameworks:
        logger.error(f'Security violation: Invalid framework: {request.framework}')
        return CheckovScanResult(
            status='error',
            working_directory=request.working_directory,
            error_message=f"Security violation: Invalid framework '{request.framework}'. Allowed frameworks are: {', '.join(allowed_frameworks)}",
            vulnerabilities=[],
            summary={},
            raw_output=None,
        )

    # Check output_format parameter for allowed values
    allowed_output_formats = [
        'cli',
        'csv',
        'cyclonedx',
        'cyclonedx_json',
        'spdx',
        'json',
        'junitxml',
        'github_failed_only',
        'gitlab_sast',
        'sarif',
    ]
    if request.output_format not in allowed_output_formats:
        logger.error(f'Security violation: Invalid output format: {request.output_format}')
        return CheckovScanResult(
            status='error',
            working_directory=request.working_directory,
            error_message=f"Security violation: Invalid output format '{request.output_format}'. Allowed formats are: {', '.join(allowed_output_formats)}",
            vulnerabilities=[],
            summary={},
            raw_output=None,
        )

    # Check for command injection patterns in check_ids and skip_check_ids
    dangerous_patterns = get_dangerous_patterns()
    logger.debug(f'Checking for {len(dangerous_patterns)} dangerous patterns')

    if request.check_ids:
        for check_id in request.check_ids:
            for pattern in dangerous_patterns:
                if pattern in check_id:
                    logger.error(
                        f"Security violation: Potentially dangerous pattern '{pattern}' in check_id: {check_id}"
                    )
                    return CheckovScanResult(
                        status='error',
                        working_directory=request.working_directory,
                        error_message=f"Security violation: Potentially dangerous pattern '{pattern}' detected in check_id",
                        vulnerabilities=[],
                        summary={},
                        raw_output=None,
                    )

    if request.skip_check_ids:
        for skip_id in request.skip_check_ids:
            for pattern in dangerous_patterns:
                if pattern in skip_id:
                    logger.error(
                        f"Security violation: Potentially dangerous pattern '{pattern}' in skip_check_id: {skip_id}"
                    )
                    return CheckovScanResult(
                        status='error',
                        working_directory=request.working_directory,
                        error_message=f"Security violation: Potentially dangerous pattern '{pattern}' detected in skip_check_id",
                        vulnerabilities=[],
                        summary={},
                        raw_output=None,
                    )

    # Build the command with Azure-specific enhancements
    # Convert working_directory to absolute path if it's not already
    working_dir = request.working_directory
    if not os.path.isabs(working_dir):
        # Get the current working directory of the MCP server
        current_dir = os.getcwd()
        # Go up to the project root directory (assuming we're in src/terraform-mcp-server/xebiams/terraform_mcp_server)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
        # Join with the requested working directory
        working_dir = os.path.abspath(os.path.join(project_root, working_dir))

    logger.info(f'Using absolute working directory: {working_dir}')
    cmd = ['checkov', '--quiet', '-d', working_dir]

    # Add framework if specified, default to terraform for Azure
    framework = request.framework or 'terraform'
    cmd.extend(['--framework', framework])

    # Auto-detect Azure compliance mode and add appropriate checks
    azure_compliance_mode = _detect_azure_compliance_mode(working_dir)
    logger.info(f'Detected Azure compliance mode: {azure_compliance_mode}')
    
    # Add Azure-specific checks based on detected compliance requirements
    if not request.check_ids:
        # Use Azure CIS checks by default for Azure infrastructure
        azure_checks = _get_azure_cis_checks()
        if azure_compliance_mode == 'cis':
            cmd.extend(['--check', ','.join(azure_checks)])
        elif azure_compliance_mode == 'security_framework':
            security_checks = _get_azure_security_framework_checks()
            cmd.extend(['--check', ','.join(azure_checks + security_checks)])
        elif azure_compliance_mode == 'microsoft_benchmark':
            benchmark_checks = _get_microsoft_cloud_benchmark_checks()
            cmd.extend(['--check', ','.join(azure_checks + benchmark_checks)])
        else:
            # Default comprehensive Azure security scan
            all_azure_checks = (azure_checks + 
                              _get_azure_security_framework_checks() + 
                              _get_microsoft_cloud_benchmark_checks())
            cmd.extend(['--check', ','.join(all_azure_checks)])
    else:
        # Use provided check IDs
        cmd.extend(['--check', ','.join(request.check_ids)])

    # Add skip check IDs if provided
    if request.skip_check_ids:
        cmd.extend(['--skip-check', ','.join(request.skip_check_ids)])

    # Add Azure provider support
    cmd.extend(['--download-external-modules', 'true'])
    
    # Set output format
    cmd.extend(['--output', request.output_format])

    # Execute command
    try:
        logger.info(f'Executing command: {" ".join(cmd)}')
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        # Clean output text
        stdout = _clean_output_text(process.stdout)
        stderr = _clean_output_text(process.stderr)

        # Debug logging
        logger.info(f'Checkov return code: {process.returncode}')
        logger.info(f'Checkov stdout: {stdout}')
        logger.info(f'Checkov stderr: {stderr}')

        # Parse results if JSON output was requested
        vulnerabilities = []
        summary = {}
        if request.output_format == 'json' and stdout:
            vulnerabilities, summary = _parse_checkov_json_output(stdout)

        # For non-JSON output, try to parse vulnerabilities from the text output
        elif stdout and process.returncode == 1:  # Return code 1 means vulnerabilities were found
            # Simple regex to extract failed checks from CLI output
            # Updated regex to handle both Windows and Unix paths
            failed_checks = re.findall(
                r'Check: (CKV[\w_]+).*?FAILED for resource: ([\w\.\-_]+).*?File: ([^:\n]+):(\d+)',
                stdout,
                re.DOTALL,
            )
            for check_id, resource, file_path, line in failed_checks:
                vuln = CheckovVulnerability(
                    id=check_id,
                    type='terraform',
                    resource=resource,
                    file_path=file_path,
                    line=int(line),
                    description=f'Failed check: {check_id}',
                    guideline=None,
                    severity='MEDIUM',
                    fixed=False,
                    fix_details=None,
                )
                vulnerabilities.append(vuln)

            # Extract summary counts
            passed_match = re.search(r'Passed checks: (\d+)', stdout)
            failed_match = re.search(r'Failed checks: (\d+)', stdout)
            skipped_match = re.search(r'Skipped checks: (\d+)', stdout)

            summary = {
                'passed': int(passed_match.group(1)) if passed_match else 0,
                'failed': int(failed_match.group(1)) if failed_match else 0,
                'skipped': int(skipped_match.group(1)) if skipped_match else 0,
            }

        # Prepare the result - consider it a success even if vulnerabilities were found
        # A return code of 1 from Checkov means vulnerabilities were found, not an error
        is_error = process.returncode not in [0, 1]
        result = CheckovScanResult(
            status='error' if is_error else 'success',
            return_code=process.returncode,
            working_directory=request.working_directory,
            vulnerabilities=vulnerabilities,
            summary=summary,
            raw_output=stdout,
        )

        return result
    except Exception as e:
        logger.error(f'Error running Checkov scan: {e}')
        return CheckovScanResult(
            status='error',
            working_directory=request.working_directory,
            error_message=str(e),
            vulnerabilities=[],
            summary={},
            raw_output=None,
        )
