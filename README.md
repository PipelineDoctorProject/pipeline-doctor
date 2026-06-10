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
docs/                   Architecture, workflows, API, remediation, reporting, and production notes
docker-compose.yml      Local development stack for API, frontend, workers, Airflow, Redis, and MLflow
.env.example            Safe template for local and production configuration
```

## Local Development

1. Copy `.env.example` to `.env` and fill local secrets.
2. Start the stack with Docker Compose.
3. Register or bootstrap a model and upload an approved baseline.
4. Trigger `opssight_daily_pipeline` in Airflow with a model id or model name and an input CSV.
5. Review incidents, RCA reports, remediation approvals, Slack alerts, and notification events in the UI.

## Production Notes

- Do not commit `.env`, runtime CSVs, MLflow artifacts, local build output, or cache files.
- Use a managed PostgreSQL/Supabase database, managed Redis/queue infrastructure, durable object storage, and a production MLflow registry.
- Keep Slack OAuth, JWT keys, SMTP credentials, database URLs, and Airflow service credentials in a secret manager.
- Run migrations through CI/CD before deploying application containers.
- Prefer separate development, staging, and production Compose/Kubernetes manifests instead of one all-purpose runtime file.

## Documentation

Start with [docs/README.md](docs/README.md), then use [docs/repository_structure.md](docs/repository_structure.md), [docs/remediation.md](docs/remediation.md), [docs/reports.md](docs/reports.md), [docs/slack.md](docs/slack.md), and [docs/schema_evolution.md](docs/schema_evolution.md) for the main production flows.
