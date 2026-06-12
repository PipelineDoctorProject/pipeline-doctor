output "container_registry_login_server" {
  description = "ACR login server."
  value       = module.platform.container_registry_login_server
}

output "container_apps_environment_id" {
  description = "Container Apps environment id."
  value       = module.platform.container_apps_environment_id
}
