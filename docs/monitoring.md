# Metrics & Monitoring (Prometheus & Grafana)

OpsSight integrates a pre-configured, production-style monitoring stack comprising **Prometheus** for metrics collection and **Grafana** for dashboard visualization. This enables teams to monitor data quality trends, API performance, Celery background worker queues, and host system resources.

---

## 1. System Architecture

```text
       ┌────────────────────────┐
       │   Celery Workers       │───┐
       └────────────────────────┘   │
       ┌────────────────────────┐   │
       │   Redis Queue          │───┼──► [Prometheus Scraping] ──► [Grafana UI]
       └────────────────────────┘   │         (Port 9090)           (Port 3000)
       ┌────────────────────────┐   │
       │   FastAPI API (/metrics)│───┘
       └────────────────────────┘
```

* **FastAPI Backend Instrumentation**: The backend uses the `prometheus-fastapi-instrumentator` package to automatically expose standard HTTP metrics (latencies, counts, status codes) under the `/metrics` endpoint.
* **Service Exporters**:
  * **Redis Exporter**: Exposes key queue statistics and memory usage from Redis.
  * **Node Exporter**: Exposes host system resource usage (CPU, Memory, Disk, Network).
  * **Celery Exporter**: Exposes Celery queue status and task execution times.

---

## 2. Local Development Setup

In local development, the monitoring services are defined in the [**`docker-compose.yml`**](file:///c:/Users/user1/Desktop/pipeline-doctor/docker-compose.yml) file.

### Accessing the UIs
* **Prometheus UI**: `http://localhost:9090`
* **Grafana UI**: `http://localhost:3001`
  * **Default Credentials**: Username `admin` / Password `admin`

### Configuration and Provisioning
All provisioning files are stored under [**`deploy/monitoring/`**](file:///c:/Users/user1/Desktop/pipeline-doctor/deploy/monitoring/):
* **Prometheus Configuration**: Located at [`deploy/monitoring/prometheus.yml`](file:///c:/Users/user1/Desktop/pipeline-doctor/deploy/monitoring/prometheus.yml). It sets up scrape targets for `api`, `redis-exporter`, and `node-exporter`.
* **Grafana Provisioning**:
  * Data sources are auto-configured to read from the local Prometheus container via [`deploy/monitoring/grafana/provisioning/datasources/prometheus.yml`](file:///c:/Users/user1/Desktop/pipeline-doctor/deploy/monitoring/grafana/provisioning/datasources/prometheus.yml).
  * Dashboards are provisioned dynamically via [`deploy/monitoring/grafana/provisioning/dashboards/dashboard.yml`](file:///c:/Users/user1/Desktop/pipeline-doctor/deploy/monitoring/grafana/provisioning/dashboards/dashboard.yml).
  * The main pre-configured dashboard JSON file is located at [`deploy/monitoring/grafana/dashboards/opssight.json`](file:///c:/Users/user1/Desktop/pipeline-doctor/deploy/monitoring/grafana/dashboards/opssight.json).

---

## 3. Production Deployment (Azure Container Apps)

OpsSight's monitoring stack can be optionally provisioned as Azure Container Apps alongside other services.

### Terraform Variables
Deployment is controlled by two variables in your environment's `variables.tf` (e.g., [`deploy/terraform/environments/prod/variables.tf`](file:///c:/Users/user1/Desktop/pipeline-doctor/deploy/terraform/environments/prod/variables.tf)):
1. `enable_monitoring` (Boolean, defaults to `false`): Set to `true` to provision Prometheus and Grafana.
2. `grafana_admin_password` (String, sensitive): Set via a GitHub Secret (`GRAFANA_ADMIN_PASSWORD`) to secure your production Grafana UI.

### Ingress & Network Security
To align with security best practices, the containers are isolated differently:
* **Grafana (Public Ingress)**:
  * Exposes public/external ingress (`external_enabled = true` on port `3000`).
  * Once deployed, the public URL is exposed as a Terraform output: `grafana_container_app_url`.
* **Prometheus (Private Ingress)**:
  * Configured with internal ingress only (`external_enabled = false` on port `9090`).
  * It is **not** accessible from the public internet. This prevents unauthorized external scraping of raw system metrics.
  * Grafana connects to Prometheus securely inside the same Container App Environment using the private FQDN:
    `http://opssight-prometheus-prod:9090`

### Accessing Prometheus UI in Production
If you ever need to access the raw Prometheus interface for debugging in production, you can port-forward it locally using the Azure CLI:
```bash
az containerapp port-forward --name opssight-prometheus-prod --resource-group opssight-prod-rg --port 9090
```
This maps the private container port directly to `http://localhost:9090` on your local machine.

---

## 4. Visualized Metrics & Dashboards

The pre-configured **OpsSight Observability Dashboard** compiles:
1. **API Performance**:
   * Request throughput (Requests/sec)
   * HTTP 2xx/3xx/4xx/5xx error rates
   * P95/P99 latency trends (fastapi instrumented endpoints)
2. **Celery Worker & Queue Sizing**:
   * Active and queued background tasks
   * Task processing times
   * Retraining job successes/failures
3. **Queue Middleware Status**:
   * Redis memory usage and connected clients
4. **Host Analytics**:
   * CPU and memory consumption per container replica
   * Disk and network I/O stats
