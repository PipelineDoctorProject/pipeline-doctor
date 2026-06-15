variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Staging resource group name."
  type        = string
}

variable "container_registry_name" {
  description = "Globally unique staging ACR name."
  type        = string
}

variable "container_apps_environment_name" {
  description = "Staging Container Apps environment name."
  type        = string
}

variable "log_analytics_workspace_name" {
  description = "Staging Log Analytics workspace name."
  type        = string
}

variable "log_retention_days" {
  description = "Log retention in days."
  type        = number
  default     = 30
}

variable "image_tag" {
  description = "Container image tag to deploy."
  type        = string
  default     = "staging-latest"
}

variable "tags" {
  description = "Additional Azure tags."
  type        = map(string)
  default     = {}
}
