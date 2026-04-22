resource "azurerm_service_plan" "app" {
  for_each            = local.roles
  name                = "${var.name}-${each.key}"
  location            = var.location
  resource_group_name = azurerm_resource_group.service.name
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = local.tags
}
