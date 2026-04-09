resource "azurerm_cosmosdb_account" "state" {
  name                          = "${var.name}-${local.suffix}"
  location                      = var.location
  resource_group_name           = azurerm_resource_group.service.name
  offer_type                    = "Standard"
  kind                          = "GlobalDocumentDB"
  public_network_access_enabled = false
  local_authentication_enabled  = false
  minimal_tls_version           = "Tls12"
  consistency_policy { consistency_level = "Session" }
  geo_location {
    location          = var.location
    failover_priority = 0
    zone_redundant    = true
  }
  backup {
    type = "Continuous"
    tier = "Continuous7Days"
  }
  tags = local.tags
  lifecycle { prevent_destroy = true }
}
resource "azurerm_cosmosdb_sql_database" "state" {
  name                = "hadoop"
  resource_group_name = azurerm_resource_group.service.name
  account_name        = azurerm_cosmosdb_account.state.name
}
