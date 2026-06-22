# OpsSight.ai Pipeline Doctor

OpsSight.ai is a production-style ML monitoring platform for validating incoming model data, detecting drift and schema changes, grouping incidents, notifying teams, and managing remediation workflows with human approval.

## What This Platform Does

- Monitors model pipeline runs from Airflow and stores tenant-scoped evidence.
- Validates schema, data quality, range, categorical, and drift signals against approved baselines.
- Groups severe signals into run-level incidents and sends real-time UI, email, and Slack notifications.
- Uses an AI RCA/reporting agent to explain what happened using stored evidence.
- Supports production-safe remediation with approval, candidate model creation, staging, promotion, and audit logs.
- Handles supervised and unsupervised remediation differently so retraining does not silently change model semantics.

## Repository Layout

```text
backend/fastapi/        FastAPI API, services, workers, models, migrations, and ML helpers
frontend/               React/Vite application for dashboards, incidents, reports, Slack, and schemas
airflow-setup/          Local Airflow DAGs and sample data for development monitoring runs
deploy/monitoring/      Prometheus configurations and Grafana provisioning/dashboards
docs/                   Architecture, workflows, API, remediation, reporting, and production notes
docker-compose.yml      Local development stack including API, frontend, Celery, Airflow, Redis, MLflow, and Prometheus/Grafana
.env.example            Safe template for local and production configuration
```

## Local Development

Development mode keeps local startup fast and convenient. The API container can
run migrations automatically, local MLflow/Airflow are started by Compose, and
the frontend runs through Vite.

```powershell
Copy-Item .env.example .env
Copy-Item backend/fastapi/.env.example backend/fastapi/.env
Copy-Item frontend/.env.example frontend/.env.local

docker compose up -d --build

cd frontend
npm install
npm run dev
```

After startup:
* **Dashboard monitoring**: You can access **Grafana** at `http://localhost:3001` (login: `admin` / `admin`) and **Prometheus** at `http://localhost:9090` to observe metrics in real time.
* **Testing pipelines**: Register or bootstrap a model, upload an approved baseline, then trigger `opssight_daily_pipeline` in Airflow with a model id/name and an input CSV path.

## Production Notes

Production mode separates one-time setup from serving traffic. Migrations and
tenant schema repair run as a release job, then API and worker replicas start
only after that job succeeds.

```powershell
Copy-Item .env.production.example .env.production
Copy-Item backend/fastapi/.env.production.example backend/fastapi/.env.production

docker compose --env-file .env.production -f docker-compose.prod.example.yml run --rm migrate
docker compose --env-file .env.production -f docker-compose.prod.example.yml up -d api worker beat frontend
```

For real hosting, keep `.env.production` values in Azure Key Vault or your
platform secret manager instead of copying files onto servers.

- Use managed PostgreSQL/Supabase, managed Redis/queue infrastructure, durable object storage, and a production MLflow registry.
- Keep Slack OAuth, JWT keys, SMTP credentials, database URLs, and Airflow service credentials in a secret manager.
- Run migrations through CI/CD before deploying application containers.
- Keep API, worker, beat, Airflow, MLflow, and frontend as separately scalable services.

## Documentation

Start with [docs/README.md](docs/README.md), then use
[docs/environment_modes.md](docs/environment_modes.md),
[docs/repository_structure.md](docs/repository_structure.md),
[docs/monitoring.md](docs/monitoring.md) (for Prometheus and Grafana details),
[docs/remediation.md](docs/remediation.md), [docs/reports.md](docs/reports.md),
[docs/slack.md](docs/slack.md), and
[docs/schema_evolution.md](docs/schema_evolution.md) for the main production
flows.
