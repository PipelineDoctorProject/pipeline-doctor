# Repository Structure

This document explains how the OpsSight.ai repository is organized for development and production review.

## Top-Level Layout

```text
backend/fastapi/        FastAPI application, Celery workers, database models, migrations, ML services
frontend/               React/Vite application used by admins and members
airflow-setup/          Development Airflow DAGs and controlled sample input data
deploy/                 Production-oriented deployment manifests and runtime config
docs/                   Product, architecture, workflow, and production-readiness documentation
docker-compose.yml      Local development orchestration
.env.example            Safe environment template
```

## Backend

The backend is organized around production service boundaries:

- `app/api/` and `app/routes/` expose HTTP and WebSocket endpoints.
- `app/services/` contains business logic for auth, tenancy, quality checks, drift, incidents, Slack, reports, remediation, and schema evolution.
- `app/tasks/` contains Celery worker tasks for RCA, scheduler monitoring, remediation, and notifications.
- `app/models/` and `app/schemas/` separate database persistence from request/response contracts.
- `alembic/` stores database migrations.

Runtime outputs such as cleaned CSVs, incoming uploads, local MLflow artifacts, and Celery beat files are intentionally ignored.

## Frontend

The frontend is organized by UI responsibility:

- `src/pages/` contains route-level screens.
- `src/components/` contains reusable cards, drawers, tables, navigation, and notification UI.
- `src/api/` centralizes backend calls.
- `src/store/` manages client-side auth and shared state.
- `src/hooks/` contains live update and reusable behavior hooks.

Generated build output (`frontend/dist`) and Vite cache (`frontend/.vite`) are not source files.

The frontend production container is built with `frontend/Dockerfile`, but from
the repository root:

```powershell
docker build -f frontend/Dockerfile -t opssight/frontend:local .
```

This keeps source UI code in `frontend/` while deployment-time Nginx config
lives in `deploy/nginx/frontend.conf`.

## Deployment

- `deploy/azure/` contains Azure Container Apps examples and environment templates.
- `deploy/nginx/` contains runtime web-server config used by the frontend container.
- `docker-compose.prod.example.yml` shows the production-style service split: migration job, API, worker, beat, and frontend.

## Airflow

`airflow-setup/dags/opssight_pipeline_dag.py` is the local development DAG that sends monitored data to OpsSight. In production, customers can run equivalent DAGs or CI jobs that call the same authenticated OpsSight ingestion APIs with model-specific configuration.

## What Should Not Be Committed

- `.env` or any real secrets.
- Runtime CSVs in `cleaned/`, `uploads/`, or backend upload folders.
- MLflow artifacts, local model binaries, and SQLite databases.
- Build outputs and dependency caches.
- Python bytecode and tool caches.

## Production Polish Still Recommended

- Add CI checks for linting, migrations, backend tests, frontend build, and Docker image build.
- Consider squashing old exploratory migrations before a first public production release.
- Rename typo-prone files such as `baselineStorre.js` after updating imports.
