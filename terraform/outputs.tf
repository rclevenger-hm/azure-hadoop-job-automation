output "resource_group_name" { value = azurerm_resource_group.service.name }
output "function_names" { value = { for k, v in azurerm_function_app_flex_consumption.app : k => v.name } }
output "api_url" { value = "https://${azurerm_function_app_flex_consumption.app["api"].default_hostname}" }
output "identity_ids" { value = { for k, v in azurerm_user_assigned_identity.app : k => v.principal_id } }
output "cosmos_account_name" { value = azurerm_cosmosdb_account.state.name }
output "queue_account_name" { value = azurerm_storage_account.queue.name }
