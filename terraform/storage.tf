resource "azurerm_storage_account" "host" {
  for_each                        = local.roles
  name                            = "hd${each.key}${local.suffix}"
  resource_group_name             = azurerm_resource_group.service.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  allow_nested_items_to_be_public = false
  public_network_access           = "Disabled"
  tags                            = local.tags
  blob_properties {
    versioning_enabled = true
    delete_retention_policy { days = 7 }
    container_delete_retention_policy { days = 7 }
  }
}
resource "azurerm_storage_account" "queue" {
  name                            = "hdqueue${local.suffix}"
  resource_group_name             = azurerm_resource_group.service.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  allow_nested_items_to_be_public = false
  public_network_access           = "Disabled"
  tags                            = local.tags
}
resource "azurerm_storage_container" "deployment" {
  for_each              = local.roles
  name                  = "deployment"
  storage_account_id    = azurerm_storage_account.host[each.key].id
  container_access_type = "private"
  depends_on            = [azurerm_private_endpoint.storage]
}
resource "azurerm_storage_queue" "jobs" {
  for_each           = toset(["jobs", "jobs-poison"])
  name               = each.key
  storage_account_id = azurerm_storage_account.queue.id
  depends_on         = [azurerm_private_endpoint.storage]
}
