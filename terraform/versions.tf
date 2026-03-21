terraform {
  required_version = ">= 1.12, < 2.0"
  backend "azurerm" { use_azuread_auth = true }
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 5.8.0" }
    random  = { source = "hashicorp/random", version = "~> 3.7" }
  }
}
