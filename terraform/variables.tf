variable "subscription_id" { type = string }
variable "tenant_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9a-f-]{36}$", var.tenant_id))
    error_message = "Use an Entra directory GUID."
  }
}
variable "api_client_id" {
  type        = string
  description = "Existing single-tenant API application client ID, with requestedAccessTokenVersion=2."
  validation {
    condition     = can(regex("^[0-9a-f-]{36}$", var.api_client_id))
    error_message = "Use the API application's client GUID."
  }
}
variable "name" {
  type    = string
  default = "hadoop-dev"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,17}$", var.name))
    error_message = "Use 3–18 lowercase letters, digits or hyphens."
  }
}
