output "resource_group_name" {
  description = "Created resource group name."
  value       = module.platform.resource_group_name
}

output "container_registry_name" {
  description = "Created Azure Container Registry name."
  value       = module.platform.container_registry_name
}

output "container_registry_login_server" {
  description = "ACR login server for image pushes."
  value       = module.platform.container_registry_login_server
}

output "container_apps_environment_id" {
  description = "Azure Container Apps environment id."
  value       = module.platform.container_apps_environment_id
}

output "api_container_app_url" {
  description = "Public FastAPI Container App URL."
  value       = module.platform.api_container_app_url
}

output "frontend_container_app_url" {
  description = "Public frontend Container App URL."
  value       = module.platform.frontend_container_app_url
}
