# PipelineDoctor Documentation

PipelineDoctor is an MLOps observability platform for:

- data quality validation
- drift detection
- automated incident creation
- AI-based root cause analysis
- live execution trace in the incident UI

---

## Documentation Index

| File | Description |
|---|---|
| [setup.md](./setup.md) | Local setup and Docker runtime guide |
| [authentication.md](./authentication.md) | JWT auth, OTP flow, and multi-tenant access |
| [data_quality.md](./data_quality.md) | Baselines, schema checks, and validation rules |
| [drift_detection.md](./drift_detection.md) | PSI, KS, drift severity, and incident escalation |
| [ml_integration.md](./ml_integration.md) | MLflow registration, loading, and feature filtering |
| [api_reference.md](./api_reference.md) | REST and WebSocket endpoint reference |
| [database_schema.md](./database_schema.md) | Core tables and relationships |
| [ai_orchestration.md](./ai_orchestration.md) | LangGraph-style RCA flow and supervisor design |
| [realtime_tracing.md](./realtime_tracing.md) | WebSocket architecture for live RCA trace and incident refresh |
| [automation_and_scheduler.md](./automation_and_scheduler.md) | Celery, Redis, doctor monitoring sweep, and Airflow integration |

---

## Week 1 Summary

Completed foundation work:

- JWT authentication with OTP verification
- schema-based multi-tenancy
- invite-based team onboarding
- baseline upload and profiling
- schema evolution tracking
- data quality checks
- MLflow model registration and loading
- drift detection and incident creation

---

## Week 2 Summary

Completed RCA and realtime work:

- LangGraph-style 4-step RCA supervisor
- structured agent state, prompt, parser, and fallback handling
- persisted `agent_runs` and `agent_step_logs`
- Celery + Redis AI execution pipeline
- scheduled doctor monitoring sweep
- incident RCA retrieval endpoints
- live WebSocket trace for RCA execution
- live incident feed for automatic incident refresh
- incident drawer RCA card and stepper UI
- AI explanation cards for Data Quality and Drift detail drawers
- unified doctor-task RCA creation so new reports always have trace logs

---

## Current Runtime Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Database | PostgreSQL / Supabase |
| ORM & Migrations | SQLAlchemy + Alembic |
| ML Registry | MLflow |
| AI RCA | LangGraph-style supervisor + Groq / fallback |
| Background Jobs | Celery + Redis |
| Realtime Layer | FastAPI WebSockets + Redis Pub/Sub |
| Workflow Orchestration | Airflow |
| Frontend | React + Vite |
