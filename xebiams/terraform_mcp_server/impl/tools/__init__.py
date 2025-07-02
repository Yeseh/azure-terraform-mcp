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

"""Tool implementations for Azure providers in the Terraform MCP server."""

from .search_azurerm_provider_docs import search_azurerm_provider_docs_impl
from .search_azuread_provider_docs import search_azuread_provider_docs_impl
from .search_azapi_provider_docs import search_azapi_provider_docs_impl
from .search_user_provided_module import search_user_provided_module_impl
from .search_azure_terraform_modules import search_azure_terraform_modules_impl
from .execute_terraform_command import execute_terraform_command_impl
from .run_checkov_scan import run_checkov_scan_impl

__all__ = [
    'search_azurerm_provider_docs_impl',
    'search_azuread_provider_docs_impl',
    'search_azapi_provider_docs_impl',
    'search_user_provided_module_impl',
    'search_azure_terraform_modules_impl',
    'execute_terraform_command_impl',
    'run_checkov_scan_impl',
]
