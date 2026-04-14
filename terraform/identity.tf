resource "azurerm_user_assigned_identity" "app" {
  for_each            = local.roles
  name                = "${var.name}-${each.key}"
  resource_group_name = azurerm_resource_group.service.name
  location            = var.location
  tags                = local.tags
}
resource "azurerm_role_assignment" "host_blob" {
  for_each             = local.roles
  scope                = azurerm_storage_account.host[each.key].id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azurerm_user_assigned_identity.app[each.key].principal_id
}
resource "azurerm_role_assignment" "host_queue" {
  for_each             = local.roles
  scope                = azurerm_storage_account.host[each.key].id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = azurerm_user_assigned_identity.app[each.key].principal_id
}
resource "azurerm_role_assignment" "queue_sender" {
  scope                = "${azurerm_storage_account.queue.id}/queueServices/default/queues/jobs"
  role_definition_name = "Storage Queue Data Message Sender"
  principal_id         = azurerm_user_assigned_identity.app["api"].principal_id
  depends_on           = [azurerm_storage_queue.jobs]
}
resource "azurerm_role_assignment" "queue_worker" {
  scope                = azurerm_storage_account.queue.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = azurerm_user_assigned_identity.app["worker"].principal_id
}
resource "azurerm_cosmosdb_sql_role_assignment" "state" {
  for_each            = local.roles
  resource_group_name = azurerm_resource_group.service.name
  account_name        = azurerm_cosmosdb_account.state.name
  role_definition_id  = "${azurerm_cosmosdb_account.state.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = azurerm_user_assigned_identity.app[each.key].principal_id
  scope               = "${azurerm_cosmosdb_account.state.id}/dbs/${azurerm_cosmosdb_sql_database.state.name}/colls/${azurerm_cosmosdb_sql_container.items.name}"
}
