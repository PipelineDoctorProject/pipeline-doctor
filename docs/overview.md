# Overview

OpsSight is a multi-tenant MLOps observability platform for monitoring production model data pipelines. It combines data quality validation, drift detection, schema evolution review, incident management, AI root-cause analysis, Slack alerting, and controlled remediation.

---

## What OpsSight Monitors

OpsSight monitors batch-oriented model runs. A run usually comes from:

- an Airflow DAG
- an uploaded CSV
- an external system calling the API

Each run is tied to:

- tenant/workspace
- model
- active baseline
- raw input file
- cleaned accepted file
- quality findings
- drift findings
- incidents
- RCA trace
- remediation state

---

## Main Product Areas

### Authentication and Tenancy

- Admin signup with OTP verification.
- Onboarding creates a workspace and tenant schema.
- Admins can invite members during onboarding or from the dashboard.
- Members join the existing tenant after password setup.
- Backend routes enforce tenant context and model ownership.

### Data Quality

- Raw validation compares incoming data to the active baseline.
- Cleaning repairs safe values and quarantines heavily corrupted rows.
- Post-clean validation decides whether prediction/drift can run.
- Failed quality gates still queue RCA for explainability.

### Schema Evolution

- Extra, missing, and changed columns become schema change evidence.
- New columns require approval before becoming part of the monitored contract.
- New string fields are not automatically used as model features.

### Drift Detection

- Drift runs only when the accepted cleaned dataset is safe enough.
- PSI and KS evidence are stored and summarized.
- Severe drift can create incidents and remediation recommendations.

### Incidents and Realtime

- Incidents are grouped by pipeline run.
- The UI centers on one top-level incident group per run.
- WebSocket updates refresh incident lists and drawers.
- Slack receives one run-level alert instead of many per-column messages.

### AI RCA

- RCA uses stored evidence from quality, drift, and schema checks.
- Agent runs and steps are persisted.
- The incident drawer shows summarized failure groups and recommended actions.

### Remediation

- Admins approve or reject remediation.
- Celery executes retraining/refitting in the background.
- Candidate models are logged to MLflow.
- Candidates are staged before deployment confirmation.
- Champion alias changes only after deployment confirmation.

---

## Runtime Architecture

```text
Frontend (React/Vite)
    |
FastAPI API
    |
PostgreSQL public schema
    |
Tenant schema per workspace
    |
Celery + Redis for background work
    |
MLflow for model registry and artifacts
    |
Airflow for scheduled/manual ingestion
    |
Slack for run-level alerts
```

---

## Production Safety Boundaries

OpsSight makes a few intentional production-safety choices:

- Backend, not frontend, enforces roles and tenant boundaries.
- Model-scoped endpoints verify ownership before returning data.
- Quality gate blocks unsafe prediction and drift.
- Remediation approval is admin-only.
- Candidate retraining does not mutate live model metadata.
- Staging and champion deployment are separate actions.
- Slack alerting is run-level to avoid alert floods.

---

## Current Local Stack

The root `docker-compose.yml` runs:

- API
- Celery worker
- Celery beat
- Redis
- PostgreSQL
- MLflow
- Airflow webserver
- Airflow scheduler

The frontend is usually run separately through Vite:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

---

## Key Documentation

- [README.md](./README.md)
- [setup.md](./setup.md)
- [authentication.md](./authentication.md)
- [data_quality.md](./data_quality.md)
- [schema_evolution.md](./schema_evolution.md)
- [remediation.md](./remediation.md)
- [model_lifecycle.md](./model_lifecycle.md)
- [automation_and_scheduler.md](./automation_and_scheduler.md)
- [slack.md](./slack.md)
