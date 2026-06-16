# Local Development Setup

This is the current recommended local setup for PipelineDoctor.

This file is intentionally focused on development mode. For the full split
between development and production runtime setup, see
[environment_modes.md](./environment_modes.md).

The project is now Docker-first for the backend stack:

- FastAPI API
- Celery worker
- Celery beat
- Redis
- MLflow
- Airflow webserver, scheduler, and DB

The frontend still runs separately with Vite.

---

## Prerequisites

| Tool | Purpose |
|---|---|
| Docker Desktop | backend stack |
| Node.js 18+ | frontend dev server |
| Git | source control |

Optional:

- Python, if you want to run backend scripts outside Docker

---

## Environment Files

OpsSight uses two local env layers. This is intentional:

- root `.env` is for Docker Compose, Airflow, and container orchestration
- `backend/fastapi/.env` is for application secrets and runtime settings
- `frontend/.env.local` is optional and only needed when overriding Vite defaults

Never commit real `.env` files. Commit only `.env.example` files.

### 1. Root Docker Compose env

Create this from the repo root:

```powershell
Copy-Item .env.example .env
```

Root `.env` owns deployment/container settings:

```env
OPSSIGHT_CONN_ID=opssight_api
AIRFLOW_VAR_OPSSIGHT_API_URL=http://api:8000
AIRFLOW_CONN_OPSSIGHT_API={"conn_type":"http","host":"http://api","port":8000,"extra":{"api_url":"http://api:8000","api_token":"replace_me_service_token"}}

AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=replace_me
AIRFLOW_ADMIN_EMAIL=admin@example.com

AIRFLOW_FERNET_KEY=replace_me
AIRFLOW_WEBSERVER_SECRET_KEY=replace_me

AIRFLOW_DB_PASSWORD=replace_me
AIRFLOW_DATABASE_SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:replace_me@airflow-db/airflow

MLFLOW_DB_PASSWORD=replace_me
MLFLOW_BACKEND_STORE_URI=postgresql+psycopg2://mlflow:replace_me@mlflow-db/mlflow
MLFLOW_ARTIFACT_ROOT=/app/mlartifacts
```

Important:

- this file should not contain one fixed model id or model name
- DAG model selection happens from Airflow trigger config or Airflow Variables
- DAG input selection happens from explicit `input_path` or `input_uri`, not by picking the latest CSV in a folder
- Airflow should authenticate to OpsSight with a dedicated service token, not a personal admin login

### 2. Backend application env

Create this from the repo root:

```powershell
Copy-Item backend/fastapi/.env.example backend/fastapi/.env
```

Minimum important values in `backend/fastapi/.env`:

```env
# Database
DB_NAME=postgres
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=5432

# JWT
SECRET_KEY=replace_with_a_real_32_plus_byte_secret
ALGORITHM=HS256

# Email
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_FROM=...
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=PipelineDoctor

# Slack
SLACK_CLIENT_ID=...
SLACK_CLIENT_SECRET=...
SLACK_REDIRECT_URI=http://localhost:8000/slack/callback

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000
REMEDIATION_CANDIDATE_MLFLOW_TRACKING_URI=http://mlflow:5000

# Optional quality overrides
DATA_QUALITY_NULL_RATIO_THRESHOLD=0.30
DATA_QUALITY_ROW_ISSUE_THRESHOLD=0.70
DATA_QUALITY_MIN_CLEAN_ROW_COUNT=10
DATA_QUALITY_MIN_CLEAN_ROW_RATIO=0.50
```

Important:

- use a real `SECRET_KEY` before production deployment
- Gmail requires an app password, not your normal mailbox password
- Slack app credentials stay here, but tenant Slack bot tokens are stored after OAuth, not hardcoded here

### 3. Optional frontend env

The frontend defaults API traffic to `http://localhost:8000` and WebSocket traffic to `ws://localhost:8000`.
Only create `frontend/.env.local` if you need different runtime endpoints:

```powershell
Copy-Item frontend/.env.example frontend/.env.local
```

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

For production builds, use your deployed endpoints:

```env
VITE_API_URL=https://api.your-domain.com
VITE_WS_URL=wss://api.your-domain.com
```

### Production env rule

In production, do not copy local `.env` files into servers. Use your hosting
platform's secret manager or environment-variable injection:

- API, worker, and beat get the backend application variables
- Airflow gets only its own admin, secret, and OpsSight connection variables
- Airflow DAG runs receive an explicit batch artifact path or pre-signed URI per run
- MLflow uses a managed backend database and durable artifact storage
- frontend gets public `VITE_*` build-time values only
- Slack workspace/channel selection is stored per tenant after OAuth
- model id/model name is passed per DAG run, not stored globally in `.env`

---

## Start The Backend Stack

From the repo root:

```bash
docker compose up -d --build
```

This starts:

- API on `http://localhost:8000`
- MLflow on `http://localhost:5000`
- Airflow on `http://localhost:8080`
- Redis on `localhost:6379`

Useful checks:

```bash
docker compose ps
docker logs --tail 100 pipeline-doctor-api
```

---

## Start The Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

---

## First-Run Product Flow

### 1. Create the first admin

1. Sign up on the frontend
2. Verify OTP
3. Go through onboarding step 1 and create the workspace
4. Stay on onboarding step 2 and invite members or skip
5. Land on the dashboard

### 2. Connect integrations

- register or verify an ML model
- upload an approved baseline
- optionally connect Slack and choose a default channel

### 3. Run monitoring

- trigger an Airflow DAG with `model_id` or `model_name` plus `input_path` or `input_uri`
- or upload a CSV through the Data Quality page / API

Example local DAG config:

```json
{
  "model_name": "spotify-kmeans-recommender",
  "input_path": "/opt/airflow/data/pure_drift_high_retraining_approval.csv"
}
```

In production, prefer a durable object-store URI or a short-lived pre-signed HTTPS URL:

```json
{
  "model_name": "spotify-kmeans-recommender",
  "input_uri": "https://storage.example.com/signed/customer-batch.csv"
}
```

---

## Local Tenant Reset

If you need to delete the current local tenant and start again, first get the authenticated user's dashboard context:

```powershell
$token = "YOUR_ACCESS_TOKEN"

$me = Invoke-RestMethod `
  -Method Get `
  -Uri "http://localhost:8000/dashboard/me" `
  -Headers @{ Authorization = "Bearer $token" }

$tenantId = $me.workspace.tenant_id
```

Then delete that tenant:

```powershell
Invoke-RestMethod `
  -Method Delete `
  -Uri "http://localhost:8000/tenant/$tenantId" `
  -Headers @{ Authorization = "Bearer $token" }
```

Use `/dashboard/me`, not `/auth/me`. The `/auth/me` endpoint is not part of the current API.

---

## Current Runtime Notes

### Data outputs

- accepted cleaned files are stored in `/app/cleaned`
- quarantined removed rows are stored in `/app/cleaned/quarantine`
- these directories are backed by the `backend_cleaned` Docker volume

### Rebuild behavior

When backend code changes, rebuild the API container:

```bash
docker compose up -d --build --force-recreate api
```

When worker-task code changes, also rebuild:

```bash
docker compose up -d --build --force-recreate celery-worker celery-beat
```

### Frontend refresh

If Vite does not pick up a change automatically:

```bash
cd frontend
npm run dev
```

---

## This Week's Runtime Hardening

The local stack now includes these stability choices:

- explicit DNS for API and worker containers
- MLflow allowed-hosts widened for container-to-container access
- Celery worker tuned down to `--concurrency=2 --max-tasks-per-child=20`
- Airflow webserver reduced to one worker
- Airflow scheduler parsing reduced for more stable local Docker behavior

---

## Daily Startup

Backend:

```bash
docker compose up -d
```

Frontend:

```bash
cd frontend
npm run dev
```

---

## Related Docs

- [README.md](./README.md)
- [environment_modes.md](./environment_modes.md)
- [authentication.md](./authentication.md)
- [data_quality.md](./data_quality.md)
- [automation_and_scheduler.md](./automation_and_scheduler.md)
- [production_deployment.md](./production_deployment.md)
- [reports.md](./reports.md)
