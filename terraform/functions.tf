resource "azurerm_service_plan" "app" {
  for_each            = local.roles
  name                = "${var.name}-${each.key}"
  location            = var.location
  resource_group_name = azurerm_resource_group.service.name
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = local.tags
}
resource "azurerm_function_app_flex_consumption" "app" {
  for_each                                       = local.roles
  name                                           = "${var.name}-${each.key}-${local.suffix}"
  location                                       = var.location
  resource_group_name                            = azurerm_resource_group.service.name
  service_plan_id                                = azurerm_service_plan.app[each.key].id
  storage_container_type                         = "blobContainer"
  storage_container_endpoint                     = "${azurerm_storage_account.host[each.key].primary_blob_endpoint}${azurerm_storage_container.deployment[each.key].name}"
  storage_authentication_type                    = "UserAssignedIdentity"
  storage_user_assigned_identity_id              = azurerm_user_assigned_identity.app[each.key].id
  runtime_name                                   = "python"
  runtime_version                                = "3.12"
  maximum_instance_count                         = var.maximum_instances
  instance_memory_in_mb                          = 2048
  http_concurrency                               = 4
  public_network_access_enabled                  = false
  https_only                                     = true
  webdeploy_publish_basic_authentication_enabled = false
  virtual_network_subnet_id                      = var.integration_subnet_id
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app[each.key].id]
  }
  site_config {
    minimum_tls_version                    = "1.2"
    scm_minimum_tls_version                = "1.2"
    application_insights_connection_string = azurerm_application_insights.service.connection_string
  }
  app_settings = {
    APP_ROLE                          = each.key
    AZURE_CLIENT_ID                   = azurerm_user_assigned_identity.app[each.key].client_id
    ENTRA_TENANT_ID                   = var.tenant_id
    TOKEN_AUDIENCE                    = var.api_client_id
    ALLOWED_CALLER_IDS                = join(",", local.callers)
    CLUSTER_PROFILES                  = jsonencode(var.profiles)
    COSMOS_ENDPOINT                   = azurerm_cosmosdb_account.state.endpoint
    COSMOS_DATABASE                   = azurerm_cosmosdb_sql_database.state.name
    COSMOS_CONTAINER                  = azurerm_cosmosdb_sql_container.items.name
    JOB_QUEUE_URL                     = "${azurerm_storage_account.queue.primary_queue_endpoint}jobs"
    DAILY_JOB_LIMIT                   = tostring(var.daily_job_limit)
    REQUESTS_PER_MINUTE               = tostring(var.requests_per_minute)
    RETENTION_DAYS                    = tostring(var.retention_days)
    FUNCTIONS_REQUEST_BODY_SIZE_LIMIT = "65536"
    AzureWebJobsStorage__accountName  = azurerm_storage_account.host[each.key].name
    AzureWebJobsStorage__credential   = "managedidentity"
    AzureWebJobsStorage__clientId     = azurerm_user_assigned_identity.app[each.key].client_id
    JobQueue__queueServiceUri         = azurerm_storage_account.queue.primary_queue_endpoint
    JobQueue__credential              = "managedidentity"
    JobQueue__clientId                = azurerm_user_assigned_identity.app[each.key].client_id
  }
  tags = local.tags
  depends_on = [azurerm_role_assignment.host_blob, azurerm_role_assignment.host_queue, azurerm_role_assignment.queue_sender,
  azurerm_role_assignment.queue_worker, azurerm_cosmosdb_sql_role_assignment.state, azurerm_private_endpoint.cosmos]
}
