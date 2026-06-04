# Local Development Setup

This is the current recommended local setup for PipelineDoctor.

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

## Environment File

Create or update:

`backend/fastapi/.env`

Minimum important values:

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

# Optional quality overrides
DATA_QUALITY_NULL_RATIO_THRESHOLD=0.30
DATA_QUALITY_ROW_ISSUE_THRESHOLD=0.70
DATA_QUALITY_MIN_CLEAN_ROW_COUNT=10
DATA_QUALITY_MIN_CLEAN_ROW_RATIO=0.50
```

Important:

- use a real `SECRET_KEY` before production deployment
- Gmail requires an app password, not your normal mailbox password

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

- trigger an Airflow DAG
- or upload a CSV through the Data Quality page / API

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
- [authentication.md](./authentication.md)
- [data_quality.md](./data_quality.md)
- [automation_and_scheduler.md](./automation_and_scheduler.md)
- [reports.md](./reports.md)
