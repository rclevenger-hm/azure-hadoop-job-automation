mock_provider "azurerm" {}
mock_provider "random" {
  mock_resource "random_id" {
    defaults = { hex = "abcd1234" }
  }
}
variables {
  subscription_id            = "00000000-0000-0000-0000-000000000000"
  tenant_id                  = "22222222-2222-2222-2222-222222222222"
  api_client_id              = "44444444-4444-4444-4444-444444444444"
  virtual_network_id         = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/platform/providers/Microsoft.Network/virtualNetworks/hadoop"
  integration_subnet_id      = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/platform/providers/Microsoft.Network/virtualNetworks/hadoop/subnets/functions"
  private_endpoint_subnet_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/platform/providers/Microsoft.Network/virtualNetworks/hadoop/subnets/endpoints"
  profiles = {
    "analytics" : {
      "cluster_name" : "your-hdinsight",
      "username" : "admin",
      "secret_id" : "https://your-hadoop-vault.vault.azure.net/secrets/cluster-password/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "allowed_callers" : [
        "11111111-1111-1111-1111-111111111111"
      ],
      "jar_prefixes" : [
        "abfss://jobs@yourstorage.dfs.core.windows.net/jars/"
      ],
      "input_prefixes" : [
        "abfss://jobs@yourstorage.dfs.core.windows.net/input/"
      ],
      "output_prefixes" : [
        "abfss://jobs@yourstorage.dfs.core.windows.net/output/"
      ],
      "status_prefix" : "abfss://jobs@yourstorage.dfs.core.windows.net/status/",
      "secret_resource_id" : "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/platform/providers/Microsoft.KeyVault/vaults/your-hadoop-vault/secrets/cluster-password"
    }
  }
  log_container_resource_ids = [
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/platform/providers/Microsoft.Storage/storageAccounts/yourstorage/blobServices/default/containers/jobs"
  ]
  alert_email       = "operator@example.com"
  budget_start_date = "2026-10-01T00:00:00Z"
}

run "private_functions" {
  command = plan
  assert {
    condition     = alltrue([for a in values(azurerm_function_app_flex_consumption.app) : !a.public_network_access_enabled && a.https_only])
    error_message = "Contract failed: private_functions."
  }
}

run "managed_identity_deployment" {
  command = plan
  assert {
    condition     = alltrue([for a in values(azurerm_function_app_flex_consumption.app) : a.storage_authentication_type == "UserAssignedIdentity" && !a.webdeploy_publish_basic_authentication_enabled])
    error_message = "Contract failed: managed_identity_deployment."
  }
}

run "isolated_trigger_roles" {
  command = plan
  assert {
    condition     = azurerm_function_app_flex_consumption.app["api"].app_settings.APP_ROLE == "api" && azurerm_function_app_flex_consumption.app["worker"].app_settings.APP_ROLE == "worker"
    error_message = "Contract failed: isolated_trigger_roles."
  }
}

run "bounded_scaling" {
  command = plan
  assert {
    condition     = alltrue([for a in values(azurerm_function_app_flex_consumption.app) : a.maximum_instance_count == 5 && a.runtime_version == "3.12"])
    error_message = "Contract failed: bounded_scaling."
  }
}

run "keyless_private_storage" {
  command = plan
  assert {
    condition     = alltrue([for a in values(azurerm_storage_account.host) : !a.shared_access_key_enabled && a.public_network_access == "Disabled" && !a.allow_nested_items_to_be_public]) && !azurerm_storage_account.queue.shared_access_key_enabled
    error_message = "Contract failed: keyless_private_storage."
  }
}

run "partitioned_state" {
  command = plan
  assert {
    condition     = azurerm_cosmosdb_sql_container.items.partition_key_paths == tolist(["/tenant"]) && azurerm_cosmosdb_sql_container.items.default_ttl == -1
    error_message = "Contract failed: partitioned_state."
  }
}

run "private_keyless_cosmos" {
  command = plan
  assert {
    condition     = !azurerm_cosmosdb_account.state.public_network_access_enabled && !azurerm_cosmosdb_account.state.local_authentication_enabled
    error_message = "Contract failed: private_keyless_cosmos."
  }
}

run "continuous_backup" {
  command = plan
  assert {
    condition     = azurerm_cosmosdb_account.state.backup[0].type == "Continuous"
    error_message = "Contract failed: continuous_backup."
  }
}

run "poison_queue" {
  command = plan
  assert {
    condition     = contains(keys(azurerm_storage_queue.jobs), "jobs-poison")
    error_message = "Contract failed: poison_queue."
  }
}

