locals {
  api_container_app_name               = coalesce(var.api_container_app_name, "opssight-api-${var.deployment_environment}")
  frontend_container_app_name          = coalesce(var.frontend_container_app_name, "opssight-frontend-${var.deployment_environment}")
  worker_container_app_name            = coalesce(var.worker_container_app_name, "opssight-worker-${var.deployment_environment}")
  beat_container_app_name              = coalesce(var.beat_container_app_name, "opssight-beat-${var.deployment_environment}")
  mlflow_container_app_name            = coalesce(var.mlflow_container_app_name, "opssight-mlflow-${var.deployment_environment}")
  airflow_webserver_container_app_name = coalesce(var.airflow_webserver_container_app_name, "opssight-airflow-webserver-${var.deployment_environment}")
  airflow_scheduler_container_app_name = coalesce(var.airflow_scheduler_container_app_name, "opssight-airflow-scheduler-${var.deployment_environment}")
  prometheus_container_app_name        = coalesce(var.prometheus_container_app_name, "opssight-prometheus-${var.deployment_environment}")
  grafana_container_app_name           = coalesce(var.grafana_container_app_name, "opssight-grafana-${var.deployment_environment}")
  redis_cache_name                     = coalesce(var.redis_cache_name, "opssight-${var.deployment_environment}-redis")
  mlflow_postgresql_server_name        = coalesce(var.mlflow_postgresql_server_name, "opssight-${var.deployment_environment}-mlflow-pg")
  airflow_postgresql_server_name       = coalesce(var.airflow_postgresql_server_name, "opssight-${var.deployment_environment}-airflow-pg")
  mlflow_storage_account_name          = coalesce(var.mlflow_storage_account_name, "opssight${var.deployment_environment}mlflow")
  mlflow_storage_container_name        = coalesce(var.mlflow_storage_container_name, "mlflow")
  app_storage_account_name             = coalesce(var.app_storage_account_name, "opssight${var.deployment_environment}app")
  app_storage_container_name           = coalesce(var.app_storage_container_name, "app-artifacts")
  frontend_public_url                  = coalesce(var.frontend_public_url, "https://${azurerm_container_app.frontend.ingress[0].fqdn}")
  mlflow_tracking_uri                  = coalesce(var.mlflow_tracking_uri, "https://${azurerm_container_app.mlflow.ingress[0].fqdn}")
  managed_mlflow_backend_store_uri     = "postgresql+psycopg2://${var.mlflow_postgresql_admin_login}:${urlencode(var.mlflow_postgresql_admin_password)}@${azurerm_postgresql_flexible_server.mlflow.fqdn}:5432/${azurerm_postgresql_flexible_server_database.mlflow.name}?sslmode=require"
  managed_mlflow_artifact_root         = "wasbs://${azurerm_storage_container.mlflow.name}@${azurerm_storage_account.mlflow.name}.blob.core.windows.net/"
  external_redis_url                   = trimspace(try(var.api_secret_environment_variables["REDIS_URL"], ""))
  use_managed_redis                    = local.external_redis_url == ""
  managed_api_secret_environment_variables = {
    AZURE_APP_STORAGE_CONNECTION_STRING = azurerm_storage_account.app.primary_connection_string
    AZURE_STORAGE_CONNECTION_STRING     = azurerm_storage_account.mlflow.primary_connection_string
  }
  api_secret_environment_variables = merge(
    local.use_managed_redis ? {
      REDIS_URL = "rediss://:${azurerm_redis_cache.this[0].primary_access_key}@${azurerm_redis_cache.this[0].hostname}:6380/0"
    } : {},
    local.managed_api_secret_environment_variables,
    var.api_secret_environment_variables
  )
  api_secret_names = toset(nonsensitive(keys(local.api_secret_environment_variables)))
  api_environment_variables = merge(
    {
      DB_MAX_OVERFLOW             = "8"
      DB_POOL_TIMEOUT             = "30"
      FRONTEND_URL                = local.frontend_public_url
      MLFLOW_TRACKING_URI         = local.mlflow_tracking_uri
      APP_STORAGE_BACKEND         = "azure_blob"
      AZURE_APP_STORAGE_CONTAINER = azurerm_storage_container.app.name
    },
    var.api_environment_variables
  )
  mlflow_environment_variables = merge(
    {
      MLFLOW_ARTIFACT_ROOT = coalesce(var.mlflow_artifact_root, local.managed_mlflow_artifact_root)
    },
    var.mlflow_environment_variables
  )
  mlflow_secret_environment_variables = merge(
    {
      MLFLOW_BACKEND_STORE_URI        = coalesce(var.mlflow_backend_store_uri, local.managed_mlflow_backend_store_uri)
      AZURE_STORAGE_CONNECTION_STRING = azurerm_storage_account.mlflow.primary_connection_string
    },
    var.mlflow_secret_environment_variables
  )
  mlflow_secret_names               = toset(nonsensitive(keys(local.mlflow_secret_environment_variables)))
  airflow_database_sql_alchemy_conn = var.enable_airflow ? "postgresql+psycopg2://${var.airflow_postgresql_admin_login}:${urlencode(var.airflow_postgresql_admin_password)}@${azurerm_postgresql_flexible_server.airflow[0].fqdn}:5432/${azurerm_postgresql_flexible_server_database.airflow[0].name}?sslmode=require" : null
  managed_airflow_secret_environment_variables = var.enable_airflow ? {
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = local.airflow_database_sql_alchemy_conn
  } : {}
  airflow_environment_variables = merge(
    {
      AIRFLOW__CORE__EXECUTOR                            = "LocalExecutor"
      AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION         = "false"
      AIRFLOW__CORE__LOAD_EXAMPLES                       = "false"
      AIRFLOW__WEBSERVER__SHOW_TRIGGER_FORM_IF_NO_PARAMS = "true"
      AIRFLOW__SCHEDULER__PARSING_PROCESSES              = "1"
      AIRFLOW_ADMIN_USERNAME                             = "admin"
      AIRFLOW_ADMIN_EMAIL                                = "admin@example.com"
    },
    var.airflow_environment_variables
  )
  airflow_secret_environment_variables = merge(
    local.managed_airflow_secret_environment_variables,
    var.airflow_secret_environment_variables
  )
  airflow_secret_names = toset(nonsensitive(keys(local.airflow_secret_environment_variables)))
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

resource "azurerm_redis_cache" "this" {
  count = local.use_managed_redis ? 1 : 0

  name                          = local.redis_cache_name
  location                      = azurerm_resource_group.this.location
  resource_group_name           = azurerm_resource_group.this.name
  capacity                      = var.redis_capacity
  family                        = var.redis_family
  sku_name                      = var.redis_sku_name
  minimum_tls_version           = "1.2"
  public_network_access_enabled = true
  non_ssl_port_enabled          = false

  tags = var.tags
}

resource "azurerm_postgresql_flexible_server" "mlflow" {
  name                          = local.mlflow_postgresql_server_name
  resource_group_name           = azurerm_resource_group.this.name
  location                      = azurerm_resource_group.this.location
  version                       = var.mlflow_postgresql_version
  administrator_login           = var.mlflow_postgresql_admin_login
  administrator_password        = var.mlflow_postgresql_admin_password
  sku_name                      = var.mlflow_postgresql_sku_name
  storage_mb                    = var.mlflow_postgresql_storage_mb
  backup_retention_days         = var.mlflow_postgresql_backup_retention_days
  public_network_access_enabled = true

  lifecycle {
    ignore_changes = [
      zone,
    ]
  }

  tags = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "mlflow" {
  name      = var.mlflow_postgresql_database_name
  server_id = azurerm_postgresql_flexible_server.mlflow.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "mlflow_allow_azure" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.mlflow.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_postgresql_flexible_server" "airflow" {
  count = var.enable_airflow ? 1 : 0

  name                          = local.airflow_postgresql_server_name
  resource_group_name           = azurerm_resource_group.this.name
  location                      = azurerm_resource_group.this.location
  version                       = var.airflow_postgresql_version
  administrator_login           = var.airflow_postgresql_admin_login
  administrator_password        = var.airflow_postgresql_admin_password
  sku_name                      = var.airflow_postgresql_sku_name
  storage_mb                    = var.airflow_postgresql_storage_mb
  backup_retention_days         = var.airflow_postgresql_backup_retention_days
  public_network_access_enabled = true

  lifecycle {
    ignore_changes = [
      zone,
    ]
  }

  tags = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "airflow" {
  count = var.enable_airflow ? 1 : 0

  name      = var.airflow_postgresql_database_name
  server_id = azurerm_postgresql_flexible_server.airflow[0].id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "airflow_allow_azure" {
  count = var.enable_airflow ? 1 : 0

  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.airflow[0].id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_storage_account" "mlflow" {
  name                            = local.mlflow_storage_account_name
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  account_tier                    = var.mlflow_storage_account_tier
  account_replication_type        = var.mlflow_storage_replication_type
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {
    delete_retention_policy {
      days = var.mlflow_storage_blob_retention_days
    }

    container_delete_retention_policy {
      days = var.mlflow_storage_blob_retention_days
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "mlflow" {
  name                  = local.mlflow_storage_container_name
  storage_account_id    = azurerm_storage_account.mlflow.id
  container_access_type = "private"
}

resource "azurerm_storage_account" "app" {
  name                            = local.app_storage_account_name
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  account_tier                    = var.app_storage_account_tier
  account_replication_type        = var.app_storage_replication_type
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {
    delete_retention_policy {
      days = var.app_storage_blob_retention_days
    }

    container_delete_retention_policy {
      days = var.app_storage_blob_retention_days
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "app" {
  name                  = local.app_storage_container_name
  storage_account_id    = azurerm_storage_account.app.id
  container_access_type = "private"
}

resource "azurerm_container_app" "api" {
  name                         = local.api_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.this.login_server
    username             = azurerm_container_registry.this.name
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
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "api"
      image  = "${azurerm_container_registry.this.login_server}/${var.api_image_name}:${var.image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      command = ["uvicorn"]
      args    = ["app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

      dynamic "env" {
        for_each = local.api_environment_variables

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
      value = local.api_secret_environment_variables[secret.value]
    }
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.this.admin_password
  }

  tags = var.tags
}

resource "azurerm_container_app" "worker" {
  name                         = local.worker_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.this.login_server
    username             = azurerm_container_registry.this.name
    password_secret_name = "acr-password"
  }

  template {
    min_replicas = var.worker_min_replicas
    max_replicas = var.worker_max_replicas

    container {
      name   = "worker"
      image  = "${azurerm_container_registry.this.login_server}/${var.api_image_name}:${var.image_tag}"
      cpu    = var.worker_cpu
      memory = var.worker_memory

      command = ["/bin/sh"]
      args    = ["-c", "celery -A app.core.celery_app:celery worker -Q ai,scheduler,emails,remediation -l info --concurrency=${var.worker_concurrency} --max-tasks-per-child=20"]

      dynamic "env" {
        for_each = local.api_environment_variables

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
      value = local.api_secret_environment_variables[secret.value]
    }
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.this.admin_password
  }

  tags = var.tags
}

resource "azurerm_container_app" "beat" {
  name                         = local.beat_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.this.login_server
    username             = azurerm_container_registry.this.name
    password_secret_name = "acr-password"
  }

  template {
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "beat"
      image  = "${azurerm_container_registry.this.login_server}/${var.api_image_name}:${var.image_tag}"
      cpu    = var.beat_cpu
      memory = var.beat_memory

      command = ["/bin/sh"]
      args    = ["-c", "celery -A app.core.celery_app:celery beat -l info --schedule /tmp/celerybeat-schedule"]

      dynamic "env" {
        for_each = local.api_environment_variables

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
      value = local.api_secret_environment_variables[secret.value]
    }
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.this.admin_password
  }

  tags = var.tags
}

resource "azurerm_container_app" "mlflow" {
  name                         = local.mlflow_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.this.login_server
    username             = azurerm_container_registry.this.name
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = var.mlflow_external_enabled
    target_port      = 5000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.mlflow_min_replicas
    max_replicas = var.mlflow_max_replicas

    container {
      name   = "mlflow"
      image  = "${azurerm_container_registry.this.login_server}/${var.api_image_name}:${var.image_tag}"
      cpu    = var.mlflow_cpu
      memory = var.mlflow_memory

      command = ["/bin/sh"]
      args    = ["-c", "if [ \"$${MLFLOW_ARTIFACT_ROOT:-/tmp/mlruns}\" = \"/tmp/mlruns\" ]; then mkdir -p /tmp/mlruns; fi; mlflow server --backend-store-uri \"$${MLFLOW_BACKEND_STORE_URI:-sqlite:////tmp/mlflow.db}\" --default-artifact-root \"$${MLFLOW_ARTIFACT_ROOT:-/tmp/mlruns}\" --workers 1 --host 0.0.0.0 --port 5000 --allowed-hosts \"*\""]

      dynamic "env" {
        for_each = local.mlflow_environment_variables

        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.mlflow_secret_names

        content {
          name        = env.value
          secret_name = lower(replace(env.value, "_", "-"))
        }
      }
    }
  }

  dynamic "secret" {
    for_each = local.mlflow_secret_names

    content {
      name  = lower(replace(secret.value, "_", "-"))
      value = local.mlflow_secret_environment_variables[secret.value]
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
    username             = azurerm_container_registry.this.name
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
    min_replicas = 1
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

resource "azurerm_container_app" "airflow_webserver" {
  count = var.enable_airflow ? 1 : 0

  name                         = local.airflow_webserver_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.this.login_server
    username             = azurerm_container_registry.this.name
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = true
    target_port      = 8080

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "airflow-webserver"
      image  = "${azurerm_container_registry.this.login_server}/${var.airflow_image_name}:${var.image_tag}"
      cpu    = var.airflow_webserver_cpu
      memory = var.airflow_webserver_memory

      command = ["/bin/bash"]
      args    = ["-c", "airflow db migrate && (airflow users create --username \"$${AIRFLOW_ADMIN_USERNAME:-admin}\" --password \"$${AIRFLOW_ADMIN_PASSWORD}\" --firstname Airflow --lastname Admin --role Admin --email \"$${AIRFLOW_ADMIN_EMAIL:-admin@example.com}\" || true) && exec airflow webserver"]

      dynamic "env" {
        for_each = local.airflow_environment_variables

        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.airflow_secret_names

        content {
          name        = env.value
          secret_name = lower(replace(env.value, "_", "-"))
        }
      }
    }
  }

  dynamic "secret" {
    for_each = local.airflow_secret_names

    content {
      name  = lower(replace(secret.value, "_", "-"))
      value = local.airflow_secret_environment_variables[secret.value]
    }
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.this.admin_password
  }

  tags = var.tags
}

resource "azurerm_container_app" "airflow_scheduler" {
  count = var.enable_airflow ? 1 : 0

  name                         = local.airflow_scheduler_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.this.login_server
    username             = azurerm_container_registry.this.name
    password_secret_name = "acr-password"
  }

  template {
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "airflow-scheduler"
      image  = "${azurerm_container_registry.this.login_server}/${var.airflow_image_name}:${var.image_tag}"
      cpu    = var.airflow_scheduler_cpu
      memory = var.airflow_scheduler_memory

      command = ["/bin/bash"]
      args    = ["-c", "airflow db migrate; exec airflow scheduler"]

      dynamic "env" {
        for_each = local.airflow_environment_variables

        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.airflow_secret_names

        content {
          name        = env.value
          secret_name = lower(replace(env.value, "_", "-"))
        }
      }
    }
  }

  dynamic "secret" {
    for_each = local.airflow_secret_names

    content {
      name  = lower(replace(secret.value, "_", "-"))
      value = local.airflow_secret_environment_variables[secret.value]
    }
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.this.admin_password
  }

  tags = var.tags
}

# ===========================================================================
# MONITORING — Prometheus + Grafana
# ===========================================================================

resource "azurerm_container_app" "prometheus" {
  count = var.enable_monitoring ? 1 : 0

  name                         = local.prometheus_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  # Internal ingress only — Grafana reaches Prometheus inside the environment.
  # Prometheus is NOT exposed to the public internet.
  ingress {
    external_enabled = false
    target_port      = 9090

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "prometheus"
      image  = "prom/prometheus:v2.53.0"
      cpu    = 0.25
      memory = "0.5Gi"

      args = [
        "--config.file=/etc/prometheus/prometheus.yml",
        "--storage.tsdb.retention.time=7d",
      ]

      env {
        name  = "API_METRICS_URL"
        value = "https://${azurerm_container_app.api.ingress[0].fqdn}"
      }

      volume_mounts {
        name = "prometheus-config"
        path = "/etc/prometheus"
      }
    }

    volume {
      name         = "prometheus-config"
      storage_type = "EmptyDir"
    }
  }

  tags = var.tags
}

resource "azurerm_container_app" "grafana" {
  count = var.enable_monitoring ? 1 : 0

  name                         = local.grafana_container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.this.name
  revision_mode                = "Single"

  ingress {
    external_enabled = true
    target_port      = 3000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "grafana"
      image  = "grafana/grafana:11.1.0"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "GF_SECURITY_ADMIN_USER"
        value = "admin"
      }

      env {
        name        = "GF_SECURITY_ADMIN_PASSWORD"
        secret_name = "grafana-admin-password"
      }

      env {
        name  = "GF_USERS_ALLOW_SIGN_UP"
        value = "false"
      }

      env {
        name  = "GF_SERVER_ROOT_URL"
        value = var.enable_monitoring ? "https://${azurerm_container_app.grafana[0].ingress[0].fqdn}" : ""
      }

      env {
        name  = "GF_AUTH_ANONYMOUS_ENABLED"
        value = "false"
      }
    }
  }

  secret {
    name  = "grafana-admin-password"
    value = var.grafana_admin_password
  }

  tags = var.tags
}
