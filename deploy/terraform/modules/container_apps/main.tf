locals {
  api_container_app_name      = coalesce(var.api_container_app_name, "opssight-api-${var.deployment_environment}")
  frontend_container_app_name = coalesce(var.frontend_container_app_name, "opssight-frontend-${var.deployment_environment}")
  api_secret_names            = toset(nonsensitive(keys(var.api_secret_environment_variables)))
}

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = var.log_analytics_workspace_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = var.tags
}

resource "azurerm_container_app_environment" "this" {
  name                       = var.container_apps_environment_name
  location                   = azurerm_resource_group.this.location
  resource_group_name        = azurerm_resource_group.this.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  tags = var.tags
}

resource "azurerm_container_registry" "this" {
  name                = var.container_registry_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = var.container_registry_sku
  admin_enabled       = true

  tags = var.tags
}

resource "azurerm_container_app" "api" {
  name                         = local.api_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.this.login_server
    username             = azurerm_container_registry.this.admin_username
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0
    max_replicas = 1

    container {
      name   = "api"
      image  = "${azurerm_container_registry.this.login_server}/${var.api_image_name}:${var.image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      command = ["uvicorn"]
      args    = ["app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

      dynamic "env" {
        for_each = var.api_environment_variables

        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.api_secret_names

        content {
          name        = env.value
          secret_name = lower(replace(env.value, "_", "-"))
        }
      }
    }
  }

  dynamic "secret" {
    for_each = local.api_secret_names

    content {
      name  = lower(replace(secret.value, "_", "-"))
      value = var.api_secret_environment_variables[secret.value]
    }
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.this.admin_password
  }

  tags = var.tags
}

resource "azurerm_container_app" "frontend" {
  name                         = local.frontend_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.this.login_server
    username             = azurerm_container_registry.this.admin_username
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = true
    target_port      = 80

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0
    max_replicas = 1

    container {
      name   = "frontend"
      image  = "${azurerm_container_registry.this.login_server}/${var.frontend_image_name}:${var.image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"

      dynamic "env" {
        for_each = var.frontend_environment_variables

        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.this.admin_password
  }

  tags = var.tags
}
