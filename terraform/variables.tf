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
variable "environment" {
  type    = string
  default = "dev"
}
variable "location" {
  type    = string
  default = "eastus"
}
variable "virtual_network_id" { type = string }
variable "integration_subnet_id" {
  type        = string
  description = "Existing subnet delegated to Microsoft.App/environments, /27 or larger; routable to HDInsight and private endpoints."
}
variable "private_endpoint_subnet_id" { type = string }
variable "profiles" {
  type = map(object({
    cluster_name       = string
    username           = string
    secret_id          = string
    secret_resource_id = string
    allowed_callers    = list(string)
    jar_prefixes       = list(string)
    input_prefixes     = list(string)
    output_prefixes    = list(string)
    status_prefix      = string
  }))
  validation {
    condition = length(var.profiles) >= 1 && length(var.profiles) <= 5 && alltrue([for k, p in var.profiles :
      can(regex("^[a-z][a-z0-9-]{2,39}$", k)) && can(regex("^[a-z][a-z0-9-]{1,57}[a-z0-9]$", p.cluster_name)) &&
      can(regex("^https://[a-zA-Z0-9-]{3,24}\\.vault\\.azure\\.net/secrets/[a-zA-Z0-9-]{1,127}/[0-9a-f]{32}$", p.secret_id)) &&
      length(p.allowed_callers) > 0 && alltrue([for c in p.allowed_callers : can(regex("^[0-9a-f-]{36}$", c))]) &&
      length(p.jar_prefixes) > 0 && length(p.input_prefixes) > 0 && length(p.output_prefixes) > 0 &&
      can(regex("^(abfss|wasbs)://[^/]+/.+/$", p.status_prefix)) &&
      alltrue([for v in concat(p.jar_prefixes, p.input_prefixes, p.output_prefixes, [p.status_prefix]) : endswith(v, "/") && !strcontains(v, "..") && !strcontains(v, "%") && !strcontains(v, "*")])
    ])
    error_message = "Profiles require bounded names, version-pinned Key Vault secrets, explicit callers, and canonical directory prefixes."
  }
}
variable "log_container_resource_ids" {
  type        = set(string)
  description = "Existing storage container ARM IDs containing profile status prefixes. API identity receives Blob Data Reader."
  validation {
    condition     = length(var.log_container_resource_ids) > 0 && alltrue([for id in var.log_container_resource_ids : can(regex("/blobServices/default/containers/[^/]+$", id))])
    error_message = "Provide exact log container resource IDs."
  }
}
