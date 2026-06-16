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
