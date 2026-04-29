output "resource_group_name" { value = azurerm_resource_group.service.name }
output "function_names" { value = { for k, v in azurerm_function_app_flex_consumption.app : k => v.name } }
