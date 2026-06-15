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
Azure Static Web Apps or frontend Container App
    |
    v
Azure Container Apps - FastAPI API
    |
    +-- Azure Container Apps - Celery worker
    +-- Azure Container Apps - Celery beat
    +-- Azure Cache for Redis
    +-- Supabase/Azure PostgreSQL
    +-- MLflow on Container Apps or managed ML registry
    +-- Azure Blob Storage for durable artifacts
```

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

---

## What To Do Next

For the current project, the next practical production steps are:

1. Move real secrets from `.env` into a secret manager or platform environment variables.
2. Configure Airflow `opssight_api` with a service identity.
3. Trigger DAGs with explicit `input_path` or `input_uri`.
4. Set frontend `VITE_API_URL` and `VITE_WS_URL` per deployment environment.
5. Move MLflow artifacts to durable storage.
6. Split migrations into a release job before running multiple API replicas.
7. Validate the complete incident-to-report-to-remediation-to-promotion flow in a staging environment.

## Azure Deployment Artifacts

Azure-specific deployment notes and env templates live in:

- `deploy/azure/README.md`
- `deploy/azure/backend-containerapp.env.example`
- `deploy/azure/frontend-build.env.example`

The repository also includes:

- `frontend/Dockerfile` for a containerized frontend deployment.
- `deploy/nginx/frontend.conf` for SPA routing and a simple `/healthz` endpoint.
- `docker-compose.prod.example.yml` as a production-style topology reference where migrations run as a separate one-shot service.
