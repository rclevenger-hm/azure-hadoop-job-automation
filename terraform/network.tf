locals {
  dns_zones = {
    blob      = "privatelink.blob.core.windows.net"
    queue     = "privatelink.queue.core.windows.net"
    cosmos    = "privatelink.documents.azure.com"
    functions = "privatelink.azurewebsites.net"
  }
  storage_endpoints = {
    api_blob     = { id = azurerm_storage_account.host["api"].id, group = "blob" }
    api_queue    = { id = azurerm_storage_account.host["api"].id, group = "queue" }
    worker_blob  = { id = azurerm_storage_account.host["worker"].id, group = "blob" }
    worker_queue = { id = azurerm_storage_account.host["worker"].id, group = "queue" }
    dispatch     = { id = azurerm_storage_account.queue.id, group = "queue" }
  }
}
resource "azurerm_private_dns_zone" "service" {
  for_each            = local.dns_zones
  name                = each.value
  resource_group_name = azurerm_resource_group.service.name
  tags                = local.tags
}
resource "azurerm_private_dns_zone_virtual_network_link" "service" {
  for_each             = local.dns_zones
  name                 = "${var.name}-${each.key}"
  private_dns_zone_id  = azurerm_private_dns_zone.service[each.key].id
  virtual_network_id   = var.virtual_network_id
  registration_enabled = false
}
