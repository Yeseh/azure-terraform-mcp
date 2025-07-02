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

"""Resource implementations for the Terraform expert."""

from .terraform_azapi_provider_resources_listing import terraform_azapi_provider_assets_listing_impl 
from .terraform_azuread_provider_resources_listing import terraform_azuread_provider_assets_listing_impl
from .terraform_azurerm_provider_resources_listing import terraform_azurerm_provider_assets_listing_impl

__all__ = [
    'terraform_azapi_provider_assets_listing_impl',
    'terraform_azuread_provider_assets_listing_impl',
    'terraform_azurerm_provider_assets_listing_impl',
]
