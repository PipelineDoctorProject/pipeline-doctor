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

variable "image_tag" {
  description = "Container image tag to deploy."
  type        = string
  default     = "dev-latest"
}

variable "api_container_app_name" {
  description = "Development FastAPI Container App name."
  type        = string
  default     = "opssight-api-dev"
}

variable "frontend_container_app_name" {
  description = "Development frontend Container App name."
  type        = string
  default     = "opssight-frontend-dev"
}

variable "worker_container_app_name" {
  description = "Development Celery worker Container App name."
  type        = string
  default     = "opssight-worker-dev"
}

variable "beat_container_app_name" {
  description = "Development Celery beat Container App name."
  type        = string
  default     = "opssight-beat-dev"
}

variable "mlflow_container_app_name" {
  description = "Development MLflow Container App name."
  type        = string
  default     = "opssight-mlflow-dev"
}

variable "enable_airflow" {
  description = "Whether to deploy development Airflow."
  type        = bool
  default     = false
}

variable "airflow_environment_variables" {
  description = "Non-secret Airflow runtime environment variables."
  type        = map(string)
  default     = {}
}

variable "airflow_secret_environment_variables" {
  description = "Secret Airflow runtime environment variables."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "airflow_postgresql_admin_password" {
  description = "Administrator password for the development Airflow PostgreSQL server."
  type        = string
  default     = null
  sensitive   = true
}

variable "redis_cache_name" {
  description = "Development Azure Cache for Redis name."
  type        = string
  default     = "opssight-dev-redis"
}

variable "mlflow_postgresql_server_name" {
  description = "Development MLflow Azure PostgreSQL Flexible Server name."
  type        = string
  default     = "opssight-dev-mlflow-pg"
}

variable "mlflow_storage_account_name" {
  description = "Development MLflow artifact storage account name."
  type        = string
  default     = "opssightdevmlflow"
}

variable "mlflow_storage_container_name" {
  description = "Development MLflow artifact blob container name."
  type        = string
  default     = "mlflow"
}

variable "app_storage_account_name" {
  description = "Development application artifact storage account name."
  type        = string
  default     = "opssightdevapp"
}

variable "app_storage_container_name" {
  description = "Development application artifact blob container name."
  type        = string
  default     = "app-artifacts"
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

variable "mlflow_postgresql_admin_password" {
  description = "Administrator password for the development MLflow PostgreSQL server."
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
