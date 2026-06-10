# OpsSight Documentation

OpsSight, previously called PipelineDoctor in parts of the codebase, is a multi-tenant MLOps observability platform. It monitors production model batches, validates incoming data, detects drift and schema changes, groups incidents at run level, runs AI root-cause analysis, and supports admin-approved remediation.

The current platform is designed around a production-style safety rule:

**Monitoring can detect and recommend automatically, but model changes require explicit human approval and staged promotion.**

---

## End-to-End Runtime Flow

```text
User or Airflow triggers a pipeline run
    |
OpsSight resolves the tenant and model
    |
Raw dataset is validated against the active baseline
    |
Cleaning and quarantine run
    |
Post-clean quality gate decides whether downstream work is safe
    |
    +-- gate failed
    |       |
    |       +-- run is marked failed
    |       +-- prediction and drift are skipped when unsafe
    |       +-- incident group is created
    |       +-- RCA is queued so the failure is explainable
    |
    +-- gate passed
            |
            +-- cleaned file is saved
            +-- prediction runs when a model is loadable
            +-- drift checks run against the active baseline
            +-- incident group is created when signals are severe enough
            +-- Slack, WebSocket, and navbar notification updates publish one run-level alert
```

---

## Remediation and Model Lifecycle Flow

```text
Incident created
    |
RCA recommends a remediation path
    |
Admin approves retraining
    |
Celery creates a candidate model in MLflow
    |
Candidate waits for promotion review
    |
Admin stages candidate
    |
MLflow alias "staging" points to the candidate version
    |
Customer deployment pipeline deploys and validates staging
    |
Admin confirms deployment
    |
MLflow alias "champion" points to the deployed version
    |
OpsSight monitors the new champion model
```

Staging and deployment confirmation are intentionally separate. Staging means "ready for external deployment." Deployment confirmation means "this version is live and should be monitored as champion."

---

## Documentation Index

| File | Purpose |
|---|---|
| [setup.md](./setup.md) | Local Docker setup, environment variables, and startup flow |
| [repository_structure.md](./repository_structure.md) | Source layout, generated artifacts, and production repo hygiene |
| [overview.md](./overview.md) | High-level product and architecture overview |
| [authentication.md](./authentication.md) | Signup, OTP, onboarding, invite flow, roles, and tenant isolation |
| [auth_and_tenant.md](./auth_and_tenant.md) | Tenant hardening workstream notes and acceptance criteria |
| [automation_and_scheduler.md](./automation_and_scheduler.md) | Airflow, Celery, Redis, scheduling, and DAG config |
| [data_quality.md](./data_quality.md) | Validation, cleaning, quarantine, and quality gate behavior |
| [schema_evolution.md](./schema_evolution.md) | Pending schema changes, approval/rejection, and feature impact |
| [drift_detection.md](./drift_detection.md) | PSI, KS, severity, and drift execution rules |
| [incidents_and_realtime.md](./incidents_and_realtime.md) | Run-level incident grouping, WebSocket updates, and alert model |
| [notifications.md](./notifications.md) | Navbar notification bell, unread counts, Slack/email context, and WebSocket delivery |
| [remediation.md](./remediation.md) | Approval, retraining, candidate staging, rejection, and deployment confirmation |
| [model_lifecycle.md](./model_lifecycle.md) | MLflow aliases, candidate/staging/champion lifecycle, and production deployment contract |
| [ml_integration.md](./ml_integration.md) | MLflow loading, feature filtering, supervised vs unsupervised behavior |
| [reports.md](./reports.md) | Production report generation, report versions, remediation-aware reporting, and PDF-style UI |
| [slack.md](./slack.md) | Slack OAuth, default channel readiness, and one-alert-per-run design |
| [ai_orchestration.md](./ai_orchestration.md) | Doctor RCA agent, final report persistence, and trace steps |
| [realtime_tracing.md](./realtime_tracing.md) | Live RCA traces and incident refresh behavior |
| [database_schema.md](./database_schema.md) | Public tables, tenant tables, and important relationships |
| [api_reference.md](./api_reference.md) | Main REST and WebSocket endpoints |

---

## Current Production-Level Capabilities

- Schema-based multi-tenancy with tenant-aware route sessions.
- Admin registration creates a workspace owner/admin.
- Onboarding supports workspace creation, invite members, and skip-to-dashboard.
- Invited members complete password setup and join the admin's tenant.
- Member users can view allowed monitoring pages, while admin-only actions stay protected.
- Model-scoped endpoints verify the model belongs to the current tenant.
- Airflow no longer relies on one hardcoded model id/name in `.env`.
- DAG runs can be model-specific through DAG trigger config or Airflow Variables.
- Data cleaning produces accepted and quarantined artifacts.
- Post-clean validation gates prediction, drift, and remediation safety.
- Run-level incident grouping prevents Slack spam from many low-level findings.
- WebSocket incident updates refresh pages without manual reloads.
- Slack delivers one top-level run alert per incident group.
- Navbar notification bell updates unread incident count from incident WebSocket events, with polling fallback.
- Notification dropdown shows recent run-level incident alerts and Slack/email delivery context.
- Full production reports summarize RCA evidence, remediation state, candidate status, and next actions.
- Remediation creates MLflow candidates without mutating the live champion.
- Candidate staging and champion deployment confirmation are split into separate human-reviewed steps.

---

## Local Development Notes

Local development uses Docker Compose for:

- FastAPI API
- Celery worker
- Celery beat
- Redis
- PostgreSQL
- MLflow
- Airflow webserver and scheduler
- Frontend through Vite

Local MLflow and Airflow are intentionally simple, but the application flow mirrors production:

- model identity comes from model registration and DAG config
- user identity comes from OpsSight auth
- workspace isolation comes from tenant schema selection
- remediation changes are staged before champion confirmation

---

## Production Expectations

In production, OpsSight should not be the system that blindly deploys models into customer serving infrastructure. The safer contract is:

- OpsSight detects issues and creates evidence.
- OpsSight can retrain or trigger a customer retraining workflow.
- OpsSight logs a candidate model with metrics and artifacts.
- OpsSight stages the candidate in MLflow.
- Customer CI/CD deploys the staging alias to serving.
- Smoke tests and health checks validate serving behavior.
- OpsSight confirms deployment and starts monitoring the champion alias.
- Realtime transports are tenant-authenticated and tenant-scoped before public multi-tenant rollout.

This keeps observability, approval, model registry, and serving deployment responsibilities cleanly separated.

Reports are part of that contract. The first report version is created after RCA, then later report versions are generated when remediation reaches important lifecycle points such as candidate creation, staging, rejection, or deployment confirmation.
