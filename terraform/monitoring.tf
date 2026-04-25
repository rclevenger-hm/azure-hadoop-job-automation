resource "azurerm_log_analytics_workspace" "service" {
  name                = "${var.name}-logs"
  location            = var.location
  resource_group_name = azurerm_resource_group.service.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = 1
  tags                = local.tags
}
resource "azurerm_application_insights" "service" {
  name                = "${var.name}-insights"
  location            = var.location
  resource_group_name = azurerm_resource_group.service.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.service.id
  tags                = local.tags
}
