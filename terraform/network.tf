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
