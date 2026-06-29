output "resource_group_name" {
  description = "Created resource group name."
  value       = azurerm_resource_group.this.name
}

output "container_registry_name" {
  description = "Created Azure Container Registry name."
  value       = azurerm_container_registry.this.name
}

output "container_registry_login_server" {
  description = "ACR login server for image pushes."
  value       = azurerm_container_registry.this.login_server
}

output "container_apps_environment_id" {
  description = "Azure Container Apps environment id."
  value       = azurerm_container_app_environment.this.id
}

output "api_container_app_url" {
  description = "Public FastAPI Container App URL."
  value       = "https://${azurerm_container_app.api.ingress[0].fqdn}"
}

output "frontend_container_app_url" {
  description = "Public frontend Container App URL."
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "worker_container_app_name" {
  description = "Celery worker Container App name."
  value       = azurerm_container_app.worker.name
}

output "beat_container_app_name" {
  description = "Celery beat Container App name."
  value       = azurerm_container_app.beat.name
}

output "mlflow_container_app_url" {
  description = "MLflow Container App URL."
  value       = "https://${azurerm_container_app.mlflow.ingress[0].fqdn}"
}

output "airflow_webserver_container_app_url" {
  description = "Airflow webserver Container App URL."
  value       = var.enable_airflow ? "https://${azurerm_container_app.airflow_webserver[0].ingress[0].fqdn}" : null
}

output "airflow_scheduler_container_app_name" {
  description = "Airflow scheduler Container App name."
  value       = var.enable_airflow ? azurerm_container_app.airflow_scheduler[0].name : null
}

output "airflow_postgresql_fqdn" {
  description = "Airflow Azure PostgreSQL Flexible Server FQDN."
  value       = var.enable_airflow ? azurerm_postgresql_flexible_server.airflow[0].fqdn : null
}

output "redis_cache_hostname" {
  description = "Azure Cache for Redis hostname."
  value       = local.use_managed_redis ? azurerm_redis_cache.this[0].hostname : null
}

output "mlflow_postgresql_fqdn" {
  description = "MLflow Azure PostgreSQL Flexible Server FQDN. Null when an external mlflow_backend_store_uri is provided."
  value       = var.mlflow_backend_store_uri == null ? azurerm_postgresql_flexible_server.mlflow[0].fqdn : null
}

output "mlflow_storage_account_name" {
  description = "MLflow artifact Storage Account name."
  value       = azurerm_storage_account.mlflow.name
}

output "mlflow_storage_container_name" {
  description = "MLflow artifact Blob container name."
  value       = azurerm_storage_container.mlflow.name
}

output "app_storage_account_name" {
  description = "Application artifact Storage Account name."
  value       = azurerm_storage_account.app.name
}

output "app_storage_container_name" {
  description = "Application artifact Blob container name."
  value       = azurerm_storage_container.app.name
}

output "grafana_container_app_url" {
  description = "Public Grafana Container App URL. Only set when enable_monitoring = true."
  value       = var.enable_monitoring ? "https://${azurerm_container_app.grafana[0].ingress[0].fqdn}" : null
}
