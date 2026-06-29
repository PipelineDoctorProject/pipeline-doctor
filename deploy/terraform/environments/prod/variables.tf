variable "location" {
  description = "Azure region."
  type        = string
  default     = "westus2"
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

variable "image_tag" {
  description = "Container image tag to deploy."
  type        = string
  default     = "prod-latest"
}

variable "api_container_app_name" {
  description = "Production FastAPI Container App name."
  type        = string
  default     = "opssight-api-prod"
}

variable "frontend_container_app_name" {
  description = "Production frontend Container App name."
  type        = string
  default     = "opssight-frontend-prod"
}

variable "worker_container_app_name" {
  description = "Production Celery worker Container App name."
  type        = string
  default     = "opssight-worker-prod"
}

variable "beat_container_app_name" {
  description = "Production Celery beat Container App name."
  type        = string
  default     = "opssight-beat-prod"
}

variable "mlflow_container_app_name" {
  description = "Production MLflow Container App name."
  type        = string
  default     = "opssight-mlflow-prod"
}

variable "enable_airflow" {
  description = "Whether to deploy production Airflow."
  type        = bool
  default     = true
}

variable "airflow_webserver_container_app_name" {
  description = "Production Airflow webserver Container App name."
  type        = string
  default     = "opssight-airflow-webserver-prod"
}

variable "airflow_scheduler_container_app_name" {
  description = "Production Airflow scheduler Container App name."
  type        = string
  default     = "opssight-airflow-scheduler-prod"
}

variable "airflow_postgresql_server_name" {
  description = "Production Airflow Azure PostgreSQL Flexible Server name."
  type        = string
  default     = "opssight-prod-airflow-pg"
}

variable "redis_cache_name" {
  description = "Production Azure Cache for Redis name."
  type        = string
  default     = "opssight-prod-redis"
}

variable "mlflow_postgresql_server_name" {
  description = "Production MLflow Azure PostgreSQL Flexible Server name."
  type        = string
  default     = "opssight-prod-mlflow-pg"
}

variable "mlflow_storage_account_name" {
  description = "Production MLflow artifact storage account name."
  type        = string
  default     = "opssightprodmlflow"
}

variable "mlflow_storage_container_name" {
  description = "Production MLflow artifact blob container name."
  type        = string
  default     = "mlflow"
}

variable "app_storage_account_name" {
  description = "Production application artifact storage account name."
  type        = string
  default     = "opssightprodapp"
}

variable "app_storage_container_name" {
  description = "Production application artifact blob container name."
  type        = string
  default     = "app-artifacts"
}

variable "api_environment_variables" {
  description = "Non-secret FastAPI runtime environment variables."
  type        = map(string)
  default = {
    APP_ENV = "production"
  }
}

variable "api_secret_environment_variables" {
  description = "Secret FastAPI runtime environment variables."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "mlflow_postgresql_admin_password" {
  description = "Administrator password for the production MLflow PostgreSQL server. Not required when mlflow_backend_store_uri is provided."
  type        = string
  default     = null
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
  description = "Administrator password for the production Airflow PostgreSQL server."
  type        = string
  default     = null
  sensitive   = true
}

variable "tags" {
  description = "Additional Azure tags."
  type        = map(string)
  default     = {}
}

variable "enable_monitoring" {
  description = "Deploy Prometheus and Grafana Container Apps."
  type        = bool
  default     = false
}

variable "grafana_admin_password" {
  description = "Grafana admin password. Set this via the TF_VAR_grafana_admin_password environment variable or a GitHub secret."
  type        = string
  sensitive   = true
  default     = "change-me-in-production"
}
