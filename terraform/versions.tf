terraform {
  required_version = ">= 1.12, < 2.0"
  backend "azurerm" { use_azuread_auth = true }
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 5.8.0" }
    random  = { source = "hashicorp/random", version = "~> 3.7" }
  }
}
provider "azurerm" {
  features {
    resource_group { prevent_deletion_if_contains_resources = true }
  }
  subscription_id                 = var.subscription_id
  storage_use_azuread             = true
  resource_provider_registrations = "none"
}
data "azurerm_client_config" "current" {}
resource "random_id" "suffix" { byte_length = 4 }
