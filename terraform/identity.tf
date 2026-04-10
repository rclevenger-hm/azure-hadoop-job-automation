resource "azurerm_user_assigned_identity" "app" {
  for_each            = local.roles
  name                = "${var.name}-${each.key}"
  resource_group_name = azurerm_resource_group.service.name
  location            = var.location
  tags                = local.tags
}
