variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Production resource group name."
  type        = string
}

variable "container_registry_name" {
  description = "Globally unique production ACR name."
  type        = string
}

variable "container_apps_environment_name" {
  description = "Production Container Apps environment name."
  type        = string
}

variable "log_analytics_workspace_name" {
  description = "Production Log Analytics workspace name."
  type        = string
}

variable "log_retention_days" {
  description = "Log retention in days."
  type        = number
  default     = 90
}

variable "tags" {
  description = "Additional Azure tags."
  type        = map(string)
  default     = {}
}
