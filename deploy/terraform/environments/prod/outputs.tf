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
