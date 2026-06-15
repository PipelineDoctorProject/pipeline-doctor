# Development and Production Modes

OpsSight supports two runtime modes:

- **Development mode** for local feature work, demos, and testing with Docker Desktop.
- **Production mode** for deployed environments where migrations, secrets, storage, and services are managed separately.

The important production rule is:

**API containers should serve traffic. They should not repair or migrate the database during startup.**

Database migrations and tenant repair run as a separate release step before API, worker, and beat containers are scaled up.

---

## File Map

| File | Mode | Purpose |
|---|---|---|
| `.env.example` | Development | Root Docker Compose, Airflow, local MLflow, and local service settings |
| `.env` | Development | Your local copy of `.env.example`; never commit |
| `backend/fastapi/.env.example` | Development | Local backend app secrets and runtime settings |
| `backend/fastapi/.env` | Development | Your local backend app env; never commit |
| `frontend/.env.example` | Development / build reference | Frontend API and WebSocket endpoint template |
| `.env.production.example` | Production-like Compose | Image names and production Compose runtime knobs |
| `.env.production` | Production-like Compose | Your production Compose copy; never commit |
| `backend/fastapi/.env.production.example` | Production | Backend production app settings template |
| `backend/fastapi/.env.production` | Production-like Compose | Your production backend env copy; never commit |

In Azure production, do not copy `.env.production` files into the server image. Put those values in Azure Container Apps environment variables and secrets, preferably backed by Key Vault.

---

## Development Mode

Use this mode when you are coding locally.

Development starts the support services you need on your machine:

- FastAPI API
- Celery worker
- Celery beat
- Redis
- local MLflow
- local Airflow
- Airflow Postgres
- MLflow Postgres

The frontend runs separately with Vite.

### 1. Create local env files

```powershell
Copy-Item .env.example .env
Copy-Item backend/fastapi/.env.example backend/fastapi/.env
Copy-Item frontend/.env.example frontend/.env.local
```

Fill the real local values in:

- `.env`
- `backend/fastapi/.env`
- `frontend/.env.local` only if the defaults need changing

### 2. Start backend services

```powershell
docker compose up -d --build
```

Local URLs:

- API: `http://localhost:8000`
- MLflow: `http://localhost:5000`
- Airflow: `http://localhost:8080`
- Redis: `localhost:6379`

### 3. Start frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

### 4. Run a DAG locally

In Airflow, trigger `opssight_daily_pipeline` with explicit config:

```json
{
  "model_name": "spotify-kmeans-recommender",
  "input_path": "/opt/airflow/data/pure_drift_high_retraining_approval.csv"
}
```

You can use either `model_id` or `model_name`.

Use `input_path` for local files mounted into Airflow. In production, use `input_uri` for object storage or a pre-signed URL.

---

## Production Mode

Use this mode when deploying a production-like stack or preparing for Azure.

Production differs from development in five important ways:

- Images are built by CI/CD and pulled by the runtime.
- Secrets are injected by the platform, not committed in files.
- Postgres, Redis, MLflow backend storage, and artifacts should be managed services.
- Database migration runs once as a release job.
- API, worker, and beat start only after the migration job succeeds.

### 1. Prepare production-like env files

For local production simulation only:

```powershell
Copy-Item .env.production.example .env.production
Copy-Item backend/fastapi/.env.production.example backend/fastapi/.env.production
```

Then replace placeholders with real values.

For Azure production, use these files as a checklist, not as deployment artifacts.

### 2. Build and push images

Example:

```powershell
docker build -t registry.example.com/opssight/backend:2026.06.12 backend/fastapi
docker build -f frontend/Dockerfile -t registry.example.com/opssight/frontend:2026.06.12 .

docker push registry.example.com/opssight/backend:2026.06.12
docker push registry.example.com/opssight/frontend:2026.06.12
```

The frontend image is built from the repository root because it copies runtime
Nginx configuration from `deploy/nginx/frontend.conf`.

### 3. Run migrations as a separate job

```powershell
docker compose --env-file .env.production -f docker-compose.prod.example.yml run --rm migrate
```

This runs:

```bash
alembic upgrade head
python scripts/repair_tenant_schemas.py
```

Only after this succeeds should the API and workers be started or updated.

### 4. Start production services

```powershell
docker compose --env-file .env.production -f docker-compose.prod.example.yml up -d api worker beat frontend
```

In Azure, the equivalent is:

- one migration Container App job
- API Container App
- worker Container App
- beat Container App
- frontend Static Web App or container

---

## Why The Modes Are Separate

Development optimizes for speed:

- Local Airflow can create its admin user automatically.
- The API can run migrations on container startup for convenience.
- Local MLflow can store artifacts in a Docker volume.
- CSV files can live in `airflow-setup/data`.

Production optimizes for safety:

- Multiple API replicas must not race on migrations.
- Secrets must not live in repository files.
- Artifacts must survive container replacement.
- Worker queues must be explicit.
- Model promotion must be auditable and reversible.

That is why production uses `docker-compose.prod.example.yml` and a separate `migrate` service.

---

## Queue Layout

OpsSight uses Celery queues by workload:

| Queue | Responsibility |
|---|---|
| `emails` | OTP and invitation email delivery |
| `ai` | RCA/report agent work |
| `scheduler` | monitoring sweeps and beat jobs |
| `remediation` | retraining, candidate creation, staging, and promotion work |

Development and production workers both listen to these queues so behavior stays consistent.

---

## Production Readiness Checklist

Before production deployment:

- Use a 32+ byte `SECRET_KEY`.
- Use managed Postgres or Supabase with SSL.
- Use managed Redis with TLS when available.
- Use production MLflow with managed backend DB and durable artifact storage.
- Configure Slack redirect URI with the production API URL.
- Configure frontend `VITE_API_URL` and `VITE_WS_URL` at build time.
- Run migration and tenant repair as a release job before API rollout.
- Keep API startup command as only `uvicorn ...`.
- Keep worker command as Celery worker only.
- Keep beat command as Celery beat only.
- Monitor API health, worker queue depth, failed tasks, MLflow failures, and Slack delivery errors.
