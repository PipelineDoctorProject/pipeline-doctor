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

  location                        = var.location
  resource_group_name             = var.resource_group_name
  container_registry_name         = var.container_registry_name
  container_registry_sku          = "Standard"
  container_apps_environment_name = var.container_apps_environment_name
  log_analytics_workspace_name    = var.log_analytics_workspace_name
  log_retention_days              = var.log_retention_days
  deployment_environment          = "prod"
  image_tag                       = var.image_tag

  tags = merge(var.tags, {
    environment = "prod"
    managed_by  = "terraform"
    project     = "opssight"
  })
}
