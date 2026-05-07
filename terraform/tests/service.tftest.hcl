mock_provider "azurerm" {}
mock_provider "random" {
  mock_resource "random_id" {
    defaults = { hex = "abcd1234" }
  }
}
