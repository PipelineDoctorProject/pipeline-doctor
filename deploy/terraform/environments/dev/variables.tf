variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Development resource group name."
  type        = string
}

variable "container_registry_name" {
  description = "Globally unique development ACR name."
  type        = string
}

variable "container_apps_environment_name" {
  description = "Development Container Apps environment name."
  type        = string
}

variable "log_analytics_workspace_name" {
  description = "Development Log Analytics workspace name."
  type        = string
}

variable "log_retention_days" {
  description = "Log retention in days."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Additional Azure tags."
  type        = map(string)
  default     = {}
}
