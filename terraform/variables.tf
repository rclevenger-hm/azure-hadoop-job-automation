variable "subscription_id" { type = string }
variable "tenant_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9a-f-]{36}$", var.tenant_id))
    error_message = "Use an Entra directory GUID."
  }
}
