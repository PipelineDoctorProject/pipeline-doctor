# PipelineDoctor Documentation

PipelineDoctor is a multi-tenant MLOps observability platform for:

- production data quality validation and cleaning
- drift detection
- grouped run-level incident management
- AI root cause analysis with live trace
- admin-approved remediation and retraining
- Slack alerting and invite-based workspace onboarding

---

## Current End-to-End Flow

```text
Airflow or UI upload
    |
Raw validation against active baseline
    |
Cleaning + row quarantine
    |
Post-clean validation gate
    |
    +--> fail gate: mark run failed, skip prediction/drift, queue RCA
    |
    +--> pass gate: save cleaned artifact, run prediction + drift, queue RCA
                |
                +--> group incidents by run
                +--> publish live incident updates
                +--> optionally deliver Slack alert
```

---

## Documentation Index

| File | Description |
|---|---|
| [setup.md](./setup.md) | Current local Docker setup and daily startup flow |
| [overview.md](./overview.md) | Current sprint overview and links to split workstream notes |
| [data_quality_workstream.md](./data_quality_workstream.md) | Current sprint data-quality gate and verification notes |
| [incidents_and_realtime.md](./incidents_and_realtime.md) | Current sprint incident grouping and live update notes |
| [remediation.md](./remediation.md) | Current sprint remediation approval and retraining notes |
| [slack.md](./slack.md) | Current sprint Slack integration and alerting notes |
| [auth_and_tenant.md](./auth_and_tenant.md) | Current sprint onboarding, invite, and tenant-hardening notes |
| [authentication.md](./authentication.md) | Signup, OTP, onboarding, invite, tokens, and tenant isolation |
| [data_quality.md](./data_quality.md) | Production cleaning gate, thresholds, quarantine, and validation rules |
| [drift_detection.md](./drift_detection.md) | Drift metrics, severity, and when drift is allowed to run |
| [ml_integration.md](./ml_integration.md) | MLflow registration, loading, and feature expectations |
| [api_reference.md](./api_reference.md) | Main REST and WebSocket endpoints |
| [database_schema.md](./database_schema.md) | Public tables, tenant tables, and run-level incident grouping |
| [ai_orchestration.md](./ai_orchestration.md) | Doctor RCA orchestration and final report persistence |
| [realtime_tracing.md](./realtime_tracing.md) | Live RCA trace and incident refresh behavior |
| [automation_and_scheduler.md](./automation_and_scheduler.md) | Celery, Airflow, Redis, and background execution flow |

---

## Sprint Progression

### Week 1

- JWT auth with OTP verification
- schema-based multi-tenancy
- baseline upload and profiling
- initial data quality checks
- MLflow model registration and loading
- drift detection and incident creation

### Week 2

- doctor RCA orchestration
- persisted `agent_runs` and `agent_step_logs`
- Celery + Redis execution path
- Airflow ingestion path
- live incident and RCA trace WebSockets
- explanation cards for Data Quality and Drift

### Week 3

- production-style data cleaning gate with quarantine output
- run-level incident grouping
- remediation API + incident drawer approval UI
- Slack workspace integration with delivery-readiness checks
- hardened onboarding, invite, and member-login flow
- stronger tenant isolation and tenant schema repair
- incident WebSocket reconnect hardening
- local Docker runtime stability improvements

---

## Current Runtime Notes

- The cleaned file stored on a run is now the accepted dataset, not just a lightly normalized copy of the raw upload.
- Drift and predictions only run when the post-clean quality gate passes.
- RCA is still queued for failed runs so blocked batches remain explainable.
- The Incidents page is centered on one top-level alert per run through `incident_groups`.
- Slack alerts are centered on the primary run-level incident instead of every low-level drift finding.
- Admins can invite members both during onboarding and from the dashboard.

---

## Current Runtime Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Database | PostgreSQL / Supabase |
| ORM and Migrations | SQLAlchemy + Alembic |
| ML Registry | MLflow |
| Background Jobs | Celery + Redis |
| Workflow Orchestration | Airflow |
| AI RCA | LangGraph-style supervisor + provider fallback |
| Realtime Layer | FastAPI WebSockets + Redis Pub/Sub |
| Frontend | React + Vite |
