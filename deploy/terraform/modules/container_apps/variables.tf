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

variable "worker_container_app_name" {
  description = "Celery worker Container App name."
  type        = string
  default     = null
}

variable "beat_container_app_name" {
  description = "Celery beat Container App name."
  type        = string
  default     = null
}

variable "mlflow_container_app_name" {
  description = "MLflow Container App name."
  type        = string
  default     = null
}

variable "enable_airflow" {
  description = "Whether to deploy self-hosted Airflow webserver and scheduler Container Apps."
  type        = bool
  default     = false
}

variable "airflow_webserver_container_app_name" {
  description = "Airflow webserver Container App name."
  type        = string
  default     = null
}

variable "airflow_scheduler_container_app_name" {
  description = "Airflow scheduler Container App name."
  type        = string
  default     = null
}

variable "airflow_postgresql_server_name" {
  description = "Azure PostgreSQL Flexible Server name for Airflow metadata."
  type        = string
  default     = null
}

variable "redis_cache_name" {
  description = "Azure Cache for Redis name."
  type        = string
  default     = null
}

variable "mlflow_postgresql_server_name" {
  description = "Azure PostgreSQL Flexible Server name for MLflow metadata."
  type        = string
  default     = null
}

variable "mlflow_storage_account_name" {
  description = "Azure Storage Account name for MLflow artifacts. Must be globally unique, lowercase, and 3-24 characters."
  type        = string
  default     = null
}

variable "mlflow_storage_container_name" {
  description = "Azure Blob container name for MLflow artifacts."
  type        = string
  default     = null
}

variable "app_storage_account_name" {
  description = "Azure Storage Account name for application uploads, cleaned data, reports, and exports. Must be globally unique, lowercase, and 3-24 characters."
  type        = string
  default     = null
}

variable "app_storage_container_name" {
  description = "Azure Blob container name for application uploads, cleaned data, reports, and exports."
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

variable "airflow_image_name" {
  description = "Airflow image repository name in ACR."
  type        = string
  default     = "opssight-airflow"
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

variable "frontend_public_url" {
  description = "Public frontend URL allowed by the FastAPI CORS configuration. Defaults to the managed Container App URL."
  type        = string
  default     = null
}

variable "mlflow_tracking_uri" {
  description = "MLflow tracking URI used by API and workers. Defaults to the managed MLflow Container App URL."
  type        = string
  default     = null
}

variable "mlflow_backend_store_uri" {
  description = "Optional external MLflow backend store URI. Defaults to the Terraform-managed Azure PostgreSQL database."
  type        = string
  default     = null
  sensitive   = true
}

variable "mlflow_artifact_root" {
  description = "Optional MLflow default artifact root. Defaults to the Terraform-managed Azure Blob container."
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

variable "airflow_postgresql_admin_login" {
  description = "Administrator login for the Airflow Azure PostgreSQL Flexible Server."
  type        = string
  default     = "airflowadmin"
}

variable "airflow_postgresql_admin_password" {
  description = "Administrator password for the Airflow Azure PostgreSQL Flexible Server."
  type        = string
  default     = null
  sensitive   = true
}

variable "airflow_postgresql_database_name" {
  description = "Airflow metadata database name."
  type        = string
  default     = "airflow"
}

variable "airflow_postgresql_version" {
  description = "Azure PostgreSQL Flexible Server version for Airflow."
  type        = string
  default     = "16"
}

variable "airflow_postgresql_sku_name" {
  description = "Azure PostgreSQL Flexible Server SKU for Airflow."
  type        = string
  default     = "B_Standard_B1ms"
}

variable "airflow_postgresql_storage_mb" {
  description = "Azure PostgreSQL Flexible Server storage size in MB for Airflow."
  type        = number
  default     = 32768
}

variable "airflow_postgresql_backup_retention_days" {
  description = "Backup retention days for the Airflow PostgreSQL server."
  type        = number
  default     = 7
}

variable "airflow_webserver_cpu" {
  description = "Airflow webserver container CPU."
  type        = number
  default     = 0.5
}

variable "airflow_webserver_memory" {
  description = "Airflow webserver container memory."
  type        = string
  default     = "1Gi"
}

variable "airflow_scheduler_cpu" {
  description = "Airflow scheduler container CPU."
  type        = number
  default     = 0.5
}

variable "airflow_scheduler_memory" {
  description = "Airflow scheduler container memory."
  type        = string
  default     = "1Gi"
}

variable "mlflow_external_enabled" {
  description = "Whether MLflow has a public ingress endpoint."
  type        = bool
  default     = false
}

variable "mlflow_min_replicas" {
  description = "Minimum MLflow replicas."
  type        = number
  default     = 0
}

variable "mlflow_max_replicas" {
  description = "Maximum MLflow replicas."
  type        = number
  default     = 1
}

variable "mlflow_cpu" {
  description = "MLflow container CPU."
  type        = number
  default     = 0.5
}

variable "mlflow_memory" {
  description = "MLflow container memory."
  type        = string
  default     = "1Gi"
}

variable "worker_min_replicas" {
  description = "Minimum Celery worker replicas."
  type        = number
  default     = 0
}

variable "worker_max_replicas" {
  description = "Maximum Celery worker replicas."
  type        = number
  default     = 1
}

variable "worker_concurrency" {
  description = "Celery worker concurrency."
  type        = number
  default     = 2
}

variable "worker_cpu" {
  description = "Celery worker container CPU."
  type        = number
  default     = 0.5
}

variable "worker_memory" {
  description = "Celery worker container memory."
  type        = string
  default     = "1Gi"
}

variable "beat_cpu" {
  description = "Celery beat container CPU."
  type        = number
  default     = 0.25
}

variable "beat_memory" {
  description = "Celery beat container memory."
  type        = string
  default     = "0.5Gi"
}

variable "redis_sku_name" {
  description = "Azure Cache for Redis SKU."
  type        = string
  default     = "Basic"
}

variable "redis_family" {
  description = "Azure Cache for Redis family."
  type        = string
  default     = "C"
}

variable "redis_capacity" {
  description = "Azure Cache for Redis capacity. 0 is C0 for Basic/Standard."
  type        = number
  default     = 0
}

variable "mlflow_postgresql_admin_login" {
  description = "Administrator login for the MLflow Azure PostgreSQL Flexible Server."
  type        = string
  default     = "mlflowadmin"
}

variable "mlflow_postgresql_admin_password" {
  description = "Administrator password for the MLflow Azure PostgreSQL Flexible Server."
  type        = string
  sensitive   = true
}

variable "mlflow_postgresql_database_name" {
  description = "MLflow metadata database name."
  type        = string
  default     = "mlflow"
}

variable "mlflow_postgresql_version" {
  description = "Azure PostgreSQL Flexible Server version for MLflow."
  type        = string
  default     = "16"
}

variable "mlflow_postgresql_sku_name" {
  description = "Azure PostgreSQL Flexible Server SKU for MLflow."
  type        = string
  default     = "B_Standard_B1ms"
}

variable "mlflow_postgresql_storage_mb" {
  description = "Azure PostgreSQL Flexible Server storage size in MB for MLflow."
  type        = number
  default     = 32768
}

variable "mlflow_postgresql_backup_retention_days" {
  description = "Backup retention days for the MLflow PostgreSQL server."
  type        = number
  default     = 7
}

variable "mlflow_storage_account_tier" {
  description = "Storage account tier for MLflow artifacts."
  type        = string
  default     = "Standard"
}

variable "mlflow_storage_replication_type" {
  description = "Storage account replication type for MLflow artifacts."
  type        = string
  default     = "LRS"
}

variable "mlflow_storage_blob_retention_days" {
  description = "Soft delete retention days for MLflow artifact blobs and containers."
  type        = number
  default     = 7
}

variable "app_storage_account_tier" {
  description = "Storage account tier for application artifacts."
  type        = string
  default     = "Standard"
}

variable "app_storage_replication_type" {
  description = "Storage account replication type for application artifacts."
  type        = string
  default     = "LRS"
}

variable "app_storage_blob_retention_days" {
  description = "Soft delete retention days for application artifact blobs and containers."
  type        = number
  default     = 7
}

variable "tags" {
  description = "Common resource tags."
  type        = map(string)
  default     = {}
}
