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

variable "api_container_app_name" {
  description = "Staging FastAPI Container App name."
  type        = string
  default     = "opssight-api-staging"
}

variable "frontend_container_app_name" {
  description = "Staging frontend Container App name."
  type        = string
  default     = "opssight-frontend-staging"
}

variable "worker_container_app_name" {
  description = "Staging Celery worker Container App name."
  type        = string
  default     = "opssight-worker-staging"
}

variable "beat_container_app_name" {
  description = "Staging Celery beat Container App name."
  type        = string
  default     = "opssight-beat-staging"
}

variable "mlflow_container_app_name" {
  description = "Staging MLflow Container App name."
  type        = string
  default     = "opssight-mlflow-staging"
}

variable "redis_cache_name" {
  description = "Staging Azure Cache for Redis name."
  type        = string
  default     = "opssight-staging-redis"
}

variable "mlflow_postgresql_server_name" {
  description = "Staging MLflow Azure PostgreSQL Flexible Server name."
  type        = string
  default     = "opssight-staging-mlflow-pg"
}

variable "mlflow_storage_account_name" {
  description = "Staging MLflow artifact storage account name."
  type        = string
  default     = "opssightstagingmlflow"
}

variable "mlflow_storage_container_name" {
  description = "Staging MLflow artifact blob container name."
  type        = string
  default     = "mlflow"
}

variable "app_storage_account_name" {
  description = "Staging application artifact storage account name."
  type        = string
  default     = "opssightstagingapp"
}

variable "app_storage_container_name" {
  description = "Staging application artifact blob container name."
  type        = string
  default     = "app-artifacts"
}

variable "api_environment_variables" {
  description = "Non-secret FastAPI runtime environment variables."
  type        = map(string)
  default = {
    APP_ENV = "staging"
  }
}

variable "api_secret_environment_variables" {
  description = "Secret FastAPI runtime environment variables."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "mlflow_postgresql_admin_password" {
  description = "Administrator password for the staging MLflow PostgreSQL server."
  type        = string
  sensitive   = true
}

variable "mlflow_backend_store_uri" {
  description = "Optional external MLflow backend store URI. Leave null to use Terraform-managed Azure PostgreSQL."
  type        = string
  default     = null
  sensitive   = true
}

variable "mlflow_artifact_root" {
  description = "Optional MLflow artifact root. Leave null to use Terraform-managed Azure Blob Storage."
  type        = string
  default     = null
}

variable "mlflow_environment_variables" {
  description = "Non-secret MLflow runtime environment variables."
  type        = map(string)
  default     = {}
}

variable "mlflow_secret_environment_variables" {
  description = "Secret MLflow runtime environment variables."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "tags" {
  description = "Additional Azure tags."
  type        = map(string)
  default     = {}
}
