output "resource_group_name" {
  description = "Created resource group name."
  value       = module.platform.resource_group_name
}

output "container_registry_name" {
  description = "Created Azure Container Registry name."
  value       = module.platform.container_registry_name
}

output "container_registry_login_server" {
  description = "ACR login server."
  value       = module.platform.container_registry_login_server
}

output "api_container_app_url" {
  description = "Public FastAPI Container App URL."
  value       = module.platform.api_container_app_url
}

output "frontend_container_app_url" {
  description = "Public frontend Container App URL."
  value       = module.platform.frontend_container_app_url
}

output "container_apps_environment_id" {
  description = "Container Apps environment id."
  value       = module.platform.container_apps_environment_id
}

output "worker_container_app_name" {
  description = "Celery worker Container App name."
  value       = module.platform.worker_container_app_name
}

output "beat_container_app_name" {
  description = "Celery beat Container App name."
  value       = module.platform.beat_container_app_name
}

output "mlflow_container_app_url" {
  description = "MLflow Container App URL."
  value       = module.platform.mlflow_container_app_url
}

output "airflow_webserver_container_app_url" {
  description = "Airflow webserver Container App URL."
  value       = module.platform.airflow_webserver_container_app_url
}

output "airflow_scheduler_container_app_name" {
  description = "Airflow scheduler Container App name."
  value       = module.platform.airflow_scheduler_container_app_name
}

output "airflow_postgresql_fqdn" {
  description = "Airflow Azure PostgreSQL Flexible Server FQDN."
  value       = module.platform.airflow_postgresql_fqdn
}

output "redis_cache_hostname" {
  description = "Azure Cache for Redis hostname."
  value       = module.platform.redis_cache_hostname
}

output "mlflow_postgresql_fqdn" {
  description = "MLflow Azure PostgreSQL Flexible Server FQDN."
  value       = module.platform.mlflow_postgresql_fqdn
}

output "mlflow_storage_account_name" {
  description = "MLflow artifact Storage Account name."
  value       = module.platform.mlflow_storage_account_name
}

output "mlflow_storage_container_name" {
  description = "MLflow artifact Blob container name."
  value       = module.platform.mlflow_storage_container_name
}

output "app_storage_account_name" {
  description = "Application artifact Storage Account name."
  value       = module.platform.app_storage_account_name
}

output "app_storage_container_name" {
  description = "Application artifact Blob container name."
  value       = module.platform.app_storage_container_name
}

output "grafana_container_app_url" {
  description = "Public Grafana Container App URL."
  value       = module.platform.grafana_container_app_url
}
