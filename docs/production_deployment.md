# Production Deployment Guide

This guide explains how to move OpsSight from the local Docker development setup toward a production-style deployment.

The main production rule is:

```text
Local Docker is for development convenience.
Production should use managed secrets, managed databases, durable artifact storage,
explicit pipeline inputs, and human-controlled model promotion.
```

---

## Production Architecture

```text
Customer training / inference pipeline
    |
    | sends explicit batch artifact metadata
    v
Airflow or customer orchestrator
    |
    | triggers OpsSight monitoring DAG with input_path/input_uri + model context
    v
OpsSight API
    |
    | validates, cleans, gates, detects drift/schema/data quality
    v
Incident + RCA + report + notifications
    |
    | optional approved remediation
    v
MLflow candidate model
    |
    | admin stages candidate
    v
Customer CI/CD deploys staging
    |
    | admin confirms deployment
    v
MLflow champion alias + future monitoring
```

For Azure, the recommended hosting split is:

```text
Azure Container Apps - frontend
    |
    v
Azure Container Apps - FastAPI API
    |
    +-- Azure Container Apps - Celery worker       (production hardening)
    +-- Azure Container Apps - Celery beat         (production hardening)
    +-- Azure Cache for Redis                      (production hardening)
    +-- Supabase/Azure PostgreSQL
    +-- MLflow on Container Apps or managed ML registry
    +-- Azure Blob Storage for durable artifacts   (production hardening)
```

---

## Current Azure Hosting Process

The current Azure deployment is managed by GitHub Actions and Terraform:

1. `Container Release` builds `opssight-api` and `opssight-frontend`.
2. The frontend image is built with `VITE_API_URL` and `VITE_WS_URL` from the selected GitHub Environment.
3. The workflow verifies the frontend bundle does not still contain `localhost:8000`.
4. Images are pushed to Azure Container Registry using an immutable `image_tag`.
5. `IaC` runs Terraform for the same environment and `image_tag`.
6. Terraform updates the API and frontend Azure Container Apps to use that image tag.
7. Terraform prints `api_container_app_url`, `frontend_container_app_url`, and ACR outputs.

Use the same image tag in both workflows. Example:

```text
Container Release: environment=dev, image_tag=dev-005, push_images=true
IaC:               environment=dev, action=apply, image_tag=dev-005
```

For real deployments, prefer immutable tags such as `dev-005`, `staging-014`, release versions, or commit SHAs. Keep `dev-latest` only as a convenience pointer, not as the tag you audit in Terraform.

The active Azure Container App revision is the source of truth for what is running. In Azure Portal, check:

```text
Container App -> Application -> Revisions and replicas -> active revision
Container App -> Application -> Containers -> Image tag
```

Production verification should include:

- ACR contains the API and frontend images for the chosen tag.
- API Container App active revision uses the chosen API image tag.
- Frontend Container App active revision uses the chosen frontend image tag.
- API `/health` returns success.
- Frontend login calls the deployed API URL, not `localhost`.

---

## What Must Change From Local Dev

| Area | Local development | Production expectation |
|---|---|---|
| App database | Docker Postgres or Supabase test project | Managed Postgres/Supabase production project with migrations controlled by release process |
| Secrets | `.env` files | Secret manager, CI variables, or platform-native secrets |
| Airflow input data | Mounted `airflow-setup/data/*.csv` | Explicit `input_uri` from object storage or an orchestrator-managed mounted path |
| Airflow auth | Workspace login/password is acceptable for testing | Scoped service account or service token, rotated regularly |
| MLflow backend | Local `mlflow-db` Postgres | Managed Postgres |
| MLflow artifacts | Local Docker volume | S3/GCS/Azure Blob or another durable artifact store |
| Frontend runtime config | Vite defaults to localhost | Build with environment-provided API and WebSocket URLs |
| Model deployment | Local alias promotion | Customer CI/CD deploys `@staging`, then OpsSight confirms `@champion` |
| Slack | Local OAuth redirect | Publicly distributed Slack app, HTTPS redirect URLs, tenant-scoped installation |

---

## Airflow Production Setup

### 1. Do not hardcode model ids or user credentials

Do not put a single global model id, model name, user email, or user password in `docker-compose.yml`.

Production model routing should come from one of:

- `dag_run.conf.model_id`
- `dag_run.conf.model_name`
- Airflow Variables for a dedicated scheduled DAG
- Airflow Connection extras
- customer orchestrator config

### 2. Always pass an explicit input artifact

The DAG now requires an input file or URL. It no longer chooses the newest CSV from the folder.

Development example:

```bash
airflow dags trigger opssight_daily_pipeline \
  --conf '{"model_name":"spotify-kmeans-recommender","input_path":"/opt/airflow/data/pure_drift_high_retraining_approval.csv"}'
```

Production example:

```bash
airflow dags trigger opssight_daily_pipeline \
  --conf '{"model_name":"spotify-kmeans-recommender","input_uri":"https://storage.example.com/batches/run-20260611.csv?<signed-query>"}'
```

This is important because production monitoring must know exactly which batch created an incident.

### 3. Use an Airflow Connection for OpsSight API auth

Connection id:

```text
opssight_api
```

Recommended production connection JSON:

```json
{
  "conn_type": "http",
  "host": "https://api.opssight.example.com",
  "extra": {
    "api_url": "https://api.opssight.example.com",
    "api_token": "SERVICE_TOKEN_FROM_SECRET_MANAGER"
  }
}
```

Development can still use:

```bash
airflow connections add opssight_api \
  --conn-type http \
  --conn-host api \
  --conn-port 8000 \
  --conn-login "admin@example.com" \
  --conn-password "local_password"
```

Production should prefer service identities over human passwords.

---

## MLflow Production Setup

Local MLflow is useful for demos and development, but production should make these changes:

1. Use a managed Postgres backend store.
2. Use durable artifact storage, not a Docker volume.
3. Keep `champion` and `staging` aliases controlled by the promotion flow.
4. Do not let remediation directly replace the live serving model.

Recommended environment shape:

```env
MLFLOW_BACKEND_STORE_URI=postgresql+psycopg2://mlflow:<secret>@<managed-postgres-host>/mlflow
MLFLOW_ARTIFACT_ROOT=s3://opssight-mlflow-artifacts
REMEDIATION_CANDIDATE_MLFLOW_TRACKING_URI=https://mlflow.opssight.example.com
```

For local development, Docker Compose still falls back to:

```text
postgresql+psycopg2://mlflow:mlflow@mlflow-db/mlflow
/app/mlartifacts
```

---

## Frontend Production Setup

The frontend source should not hardcode deployed API hosts. Build-time endpoints are controlled by Vite environment variables.

Development example:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

Production example:

```env
VITE_API_URL=https://api.opssight.example.com
VITE_WS_URL=wss://api.opssight.example.com
```

These `VITE_*` values are public build-time configuration, not secrets. If the frontend and API are hosted on different domains, configure backend CORS and `FRONTEND_URL` to match the deployed frontend origin.

In GitHub Environments, set:

- `VITE_API_URL=https://<api-container-app-url>`
- `VITE_WS_URL=wss://<api-container-app-host>`

After changing these values, rebuild the frontend image with `Container Release`, then apply the same image tag with `IaC`. Vite values are baked into the frontend image at build time, so changing GitHub Environment values alone does not change an already-built frontend container.

The API `FRONTEND_URL` is managed by Terraform from the frontend Container App URL so CORS follows the deployed frontend origin.

---

## Database and Migration Rules

Production migrations should be run as a release step, not accidentally by every API replica.

Recommended production flow:

1. Build image.
2. Run tests.
3. Run `alembic upgrade head` once as a deployment job.
4. Run `python scripts/repair_tenant_schemas.py` in the same one-shot migration job.
5. Start API replicas.
6. Start workers.
7. Start scheduler/beat.

The local Docker setup may still run migrations automatically for speed, but production should avoid multiple app containers racing on migrations or tenant repair.

Production API startup should only start the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

---

## Slack Production Setup

Slack must be installed per customer workspace.

Production checklist:

1. Enable Slack public distribution when marketplace prerequisites are complete.
2. Use HTTPS OAuth redirect URLs.
3. Store Slack bot token per tenant.
4. Validate returned Slack `team.id` against the tenant's expected workspace/team id when provided.
5. Show connected workspace and disconnect action in the UI.
6. Send one run-level incident alert per incident group.

---

## Production Readiness Checklist

- `.env` files are not committed with real secrets.
- Airflow DAG runs include `input_path` or `input_uri`.
- Airflow API auth uses service token or service account credentials.
- Airflow and MLflow databases are externalized.
- MLflow artifacts are stored in durable object storage.
- Frontend builds use environment-provided `VITE_API_URL` and `VITE_WS_URL`.
- Backend migrations are controlled by deployment.
- Tenant isolation is verified on every protected route.
- Slack installs are tenant-scoped.
- WebSocket and notification events are tenant-scoped.
- Remediation creates candidates, not direct live replacements.
- Staging and champion promotion are auditable.
- Reports include RCA, remediation lifecycle, candidate, staging, and deployment state.
- GitHub `prod` environment requires reviewer approval.
- Terraform state is remote and protected.
- Container Apps use immutable image tags for every release.
- ACR authentication uses managed identity and `AcrPull` in production where the deployment principal has permission to create role assignments. The current dev fallback can use ACR admin credentials.
- API runtime secrets come from GitHub Environment secrets, Azure Key Vault, or Container App secrets, never from committed `.env` files.

---

## What To Do Next

For the current project, the next practical production steps are:

1. Configure remote Terraform state before any production apply.
2. Move production secrets from `.env` into GitHub Environment secrets or Azure Key Vault.
3. Add a one-shot migration job for `alembic upgrade head` and tenant repair.
4. Add Terraform-managed worker and beat Container Apps.
5. Add Redis and durable Blob Storage for queues, uploads, cleaned data, reports, and artifacts.
6. Configure Airflow `opssight_api` with a service identity.
7. Trigger DAGs with explicit `input_path` or `input_uri`.
8. Configure production custom domains, HTTPS, and Slack OAuth redirect URLs.
9. Validate the complete incident-to-report-to-remediation-to-promotion flow in staging before promoting the same image tag to production.

## Azure Deployment Artifacts

Azure-specific deployment notes and env templates live in:

- `deploy/azure/README.md`
- `deploy/azure/backend-containerapp.env.example`
- `deploy/azure/frontend-build.env.example`

The repository also includes:

- `frontend/Dockerfile` for a containerized frontend deployment.
- `deploy/nginx/frontend.conf` for SPA routing and a simple `/healthz` endpoint.
- `docker-compose.prod.example.yml` as a production-style topology reference where migrations run as a separate one-shot service.
