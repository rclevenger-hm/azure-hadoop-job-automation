resource "azurerm_cosmosdb_account" "state" {
  name                          = "${var.name}-${local.suffix}"
  location                      = var.location
  resource_group_name           = azurerm_resource_group.service.name
  offer_type                    = "Standard"
  kind                          = "GlobalDocumentDB"
  public_network_access_enabled = false
  local_authentication_disabled = true
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
resource "azurerm_cosmosdb_sql_container" "items" {
  name                  = "items"
  resource_group_name   = azurerm_resource_group.service.name
  account_name          = azurerm_cosmosdb_account.state.name
  database_name         = azurerm_cosmosdb_sql_database.state.name
  partition_key_paths   = ["/tenant"]
  partition_key_version = 2
  default_ttl           = -1
  autoscale_settings { max_throughput = 1000 }
  indexing_policy {
    indexing_mode = "consistent"
    included_path { path = "/*" }
    excluded_path { path = "/request/*" }
    excluded_path { path = "/profile/*" }
    composite_index {
      index {
        path  = "/created_at"
        order = "descending"
      }
      index {
        path  = "/id"
        order = "descending"
      }
    }
    composite_index {
      index {
        path  = "/next_check"
        order = "ascending"
      }
      index {
        path  = "/id"
        order = "ascending"
      }
    }
  }
  lifecycle { prevent_destroy = true }
}
