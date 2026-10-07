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
resource "azurerm_monitor_action_group" "operators" {
  name                = "${var.name}-operators"
  resource_group_name = azurerm_resource_group.service.name
  short_name          = "hadoop"
  email_receiver {
    name          = "operator"
    email_address = var.alert_email
  }
  tags = local.tags
}
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "errors" {
  name                 = "${var.name}-review-or-errors"
  resource_group_name  = azurerm_resource_group.service.name
  location             = var.location
  evaluation_frequency = "PT5M"
  window_duration      = "PT5M"
  scopes               = [azurerm_log_analytics_workspace.service.id]
  severity             = 2
  criteria {
    query                   = "AppTraces | where Message has 'NEEDS_REVIEW' or Message has 'api_error' or Message has 'reconcile_complete' and Message !has '\"failed\": 0'"
    time_aggregation_method = "Count"
    threshold               = 0
    operator                = "GreaterThan"
    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }
  action { action_groups = [azurerm_monitor_action_group.operators.id] }
  tags = local.tags
}
resource "azurerm_monitor_metric_alert" "queue" {
  name                = "${var.name}-queue-backlog"
  resource_group_name = azurerm_resource_group.service.name
  scopes              = ["${azurerm_storage_account.queue.id}/queueServices/default"]
  severity            = 2
  frequency           = "PT1H"
  window_size         = "PT1H"
  criteria {
    metric_namespace = "Microsoft.Storage/storageAccounts/queueServices"
    metric_name      = "QueueMessageCount"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 20
  }
  action { action_group_id = azurerm_monitor_action_group.operators.id }
  tags = local.tags
}
resource "azurerm_consumption_budget_resource_group" "service" {
  name              = "${var.name}-monthly"
  resource_group_id = azurerm_resource_group.service.id
  amount            = var.monthly_budget
  time_grain        = "Monthly"
  time_period { start_date = var.budget_start_date }
  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThanOrEqualTo"
    contact_emails = [var.alert_email]
  }
}
