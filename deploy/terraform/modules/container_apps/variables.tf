variable "location" {
  description = "Azure region for all resources."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name."
  type        = string
}

variable "container_registry_name" {
  description = "Globally unique Azure Container Registry name."
  type        = string
}

variable "container_registry_sku" {
  description = "Azure Container Registry SKU."
  type        = string
  default     = "Basic"
}

variable "container_apps_environment_name" {
  description = "Azure Container Apps managed environment name."
  type        = string
}

variable "log_analytics_workspace_name" {
  description = "Log Analytics workspace name."
  type        = string
}

variable "log_retention_days" {
  description = "Log Analytics retention period."
  type        = number
  default     = 30
}

variable "deployment_environment" {
  description = "Application deployment environment name."
  type        = string
  default     = "dev"
}

variable "image_tag" {
  description = "Container image tag to deploy."
  type        = string
  default     = "dev-latest"
}

variable "api_container_app_name" {
  description = "FastAPI Container App name."
  type        = string
  default     = null
}

variable "frontend_container_app_name" {
  description = "Frontend Container App name."
  type        = string
  default     = null
}

variable "api_image_name" {
  description = "FastAPI image repository name in ACR."
  type        = string
  default     = "opssight-api"
}

variable "frontend_image_name" {
  description = "Frontend image repository name in ACR."
  type        = string
  default     = "opssight-frontend"
}

variable "api_environment_variables" {
  description = "Non-secret FastAPI runtime environment variables."
  type        = map(string)
  default = {
    APP_ENV = "development"
  }
}

variable "api_secret_environment_variables" {
  description = "Secret FastAPI runtime environment variables."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "frontend_environment_variables" {
  description = "Non-secret frontend container environment variables."
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Common resource tags."
  type        = map(string)
  default     = {}
}
