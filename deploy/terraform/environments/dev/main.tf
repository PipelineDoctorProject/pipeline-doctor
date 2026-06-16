terraform {
  required_version = ">= 1.9.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

module "platform" {
  source = "../../modules/container_apps"

  location                            = var.location
  resource_group_name                 = var.resource_group_name
  container_registry_name             = var.container_registry_name
  container_apps_environment_name     = var.container_apps_environment_name
  log_analytics_workspace_name        = var.log_analytics_workspace_name
  log_retention_days                  = var.log_retention_days
  deployment_environment              = "dev"
  image_tag                           = var.image_tag
  api_container_app_name              = var.api_container_app_name
  frontend_container_app_name         = var.frontend_container_app_name
  worker_container_app_name           = var.worker_container_app_name
  beat_container_app_name             = var.beat_container_app_name
  mlflow_container_app_name           = var.mlflow_container_app_name
  redis_cache_name                    = var.redis_cache_name
  mlflow_postgresql_server_name       = var.mlflow_postgresql_server_name
  mlflow_storage_account_name         = var.mlflow_storage_account_name
  mlflow_storage_container_name       = var.mlflow_storage_container_name
  api_environment_variables           = var.api_environment_variables
  api_secret_environment_variables    = var.api_secret_environment_variables
  mlflow_postgresql_admin_password    = var.mlflow_postgresql_admin_password
  mlflow_backend_store_uri            = var.mlflow_backend_store_uri
  mlflow_artifact_root                = var.mlflow_artifact_root
  mlflow_environment_variables        = var.mlflow_environment_variables
  mlflow_secret_environment_variables = var.mlflow_secret_environment_variables

  tags = merge(var.tags, {
    environment = "dev"
    managed_by  = "terraform"
    project     = "opssight"
  })
}
