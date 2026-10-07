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
resource "azurerm_private_endpoint" "storage" {
  for_each            = local.storage_endpoints
  name                = "${var.name}-${each.key}"
  resource_group_name = azurerm_resource_group.service.name
  location            = var.location
  subnet_id           = var.private_endpoint_subnet_id
  private_service_connection {
    name                           = each.key
    private_connection_resource_id = each.value.id
    subresource_names              = [each.value.group]
    is_manual_connection           = false
  }
  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [azurerm_private_dns_zone.service[each.value.group].id]
  }
  tags = local.tags
}
resource "azurerm_private_endpoint" "cosmos" {
  name                = "${var.name}-cosmos"
  resource_group_name = azurerm_resource_group.service.name
  location            = var.location
  subnet_id           = var.private_endpoint_subnet_id
  private_service_connection {
    name                           = "cosmos"
    private_connection_resource_id = azurerm_cosmosdb_account.state.id
    subresource_names              = ["Sql"]
    is_manual_connection           = false
  }
  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [azurerm_private_dns_zone.service["cosmos"].id]
  }
  tags = local.tags
}
resource "azurerm_private_endpoint" "functions" {
  for_each            = local.roles
  name                = "${var.name}-${each.key}-app"
  resource_group_name = azurerm_resource_group.service.name
  location            = var.location
  subnet_id           = var.private_endpoint_subnet_id
  private_service_connection {
    name                           = each.key
    private_connection_resource_id = azurerm_function_app_flex_consumption.app[each.key].id
    subresource_names              = ["sites"]
    is_manual_connection           = false
  }
  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [azurerm_private_dns_zone.service["functions"].id]
  }
  tags = local.tags
}
