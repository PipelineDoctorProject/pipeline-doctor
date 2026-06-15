# Automation and Scheduling

This document explains how PipelineDoctor uses Airflow, Celery, and Redis in the current setup.

---

## Current Background Flow

```text
Airflow or UI upload
    |
FastAPI quality pipeline
    |
raw validation -> cleaning -> quarantine -> post-clean gate
    |
    +--> gate fail: mark run failed, queue RCA
    |
    +--> gate pass: predictions -> drift -> queue RCA
                               |
                               +--> grouped incidents
                               +--> optional Slack alert
```

Heavy or asynchronous work is handled by Celery workers.

---

## Runtime Components

| Component | Purpose |
|---|---|
| FastAPI API | request entry point |
| Redis | Celery broker, result backend, Pub/Sub bridge |
| Celery worker | RCA, remediation, scheduled jobs, email |
| Celery beat | scheduler heartbeat and doctor sweep |
| Airflow | external pipeline trigger path |

---

## Celery Worker Responsibilities

The worker currently handles:

- doctor RCA execution
- remediation execution
- scheduled monitoring tasks
- email tasks

### Doctor RCA

The doctor task is the single owner of new RCA persistence:

1. create `AgentRun`
2. publish live step updates
3. write `AgentStepLog`
4. persist the final RCA incident/report

### Remediation

Approved remediation runs execute through the worker and write:

- `remediation_runs`
- `remediation_action_logs`

---

## Celery Beat Responsibilities

Celery Beat currently dispatches:

- `record_beat_heartbeat`
- `trigger_doctor_monitoring`

### Beat heartbeat

Beat writes a heartbeat into Redis so health endpoints can detect whether scheduling is alive.

Redis key:

`celery:beat:last_heartbeat`

---

## Doctor Monitoring Sweep

The scheduled doctor sweep:

1. loops through tenants
2. enters each tenant schema
3. finds the latest run
4. checks whether a doctor `AgentRun` already exists
5. queues RCA only when needed

This avoids duplicate RCA runs for the same latest batch.

In addition to the scheduled sweep, the validation pipeline queues RCA immediately after the quality pipeline finishes its own allowed work.

Important:

- the doctor task can still be queued when the quality gate fails
- that allows failed runs to produce trace-backed RCA instead of silently stopping

---

## Airflow Integration

The Airflow DAG:

1. resolves an explicit input CSV path or HTTPS URL
2. authenticates to the OpsSight API using an Airflow Connection
3. sends the file to `/data-quality/validate` with a resolved model id, or `/data-quality/validate-auto`

The DAG intentionally does not pick the newest CSV from the local folder. Every run must say which batch artifact it is validating. This keeps incident evidence traceable in production.

### Production auth rule

Do not hardcode API credentials or JWT tokens in `docker-compose.yml`.

Use Airflow Connection `opssight_api` instead:

- connection type: `http`
- host: `api`
- port: `8000`
- development auth option: login/password
- production auth option: set `extra.api_token` for service-token style auth

Connection id can be overridden with:

- `OPSSIGHT_CONN_ID` (defaults to `opssight_api`)

### Model routing rule

Model targeting is now runtime-driven:

1. `dag_run.conf.model_id` (highest priority)
2. Airflow Variable `opssight_model_id`
3. connection extra `model_id`
4. `dag_run.conf.model_name`
5. Airflow Variable `opssight_model_name`
6. connection extra `model_name`
7. fallback to `/data-quality/validate-auto` (schema-based matching)

Do not set a model id/name in the root `.env` for production. That would make the whole Airflow deployment point at one model. Use DAG trigger config for ad-hoc runs, or Airflow Variables/Connection extras for a specific scheduled pipeline.

### Access token rule

When using login/password, the DAG should:

1. call `POST /auth/login`
2. read the returned `access_token`
3. call the validation endpoint

This avoids static long-lived tokens in code/config.

### Input artifact rule

Every DAG run must provide one of:

1. `dag_run.conf.input_path`
2. `dag_run.conf.input_uri`

Development path example:

```json
{
  "model_name": "spotify-kmeans-recommender",
  "input_path": "/opt/airflow/data/pure_drift_high_retraining_approval.csv"
}
```

Production URI example:

```json
{
  "model_name": "spotify-kmeans-recommender",
  "input_uri": "https://storage.example.com/batches/run-20260611.csv?<signed-query>"
}
```

Unsupported object-store schemes such as `s3://` should be converted to pre-signed HTTPS URLs or mounted into the Airflow worker filesystem by the platform.

---

## Local Docker Runtime Notes

The root `docker-compose.yml` is the active backend compose file.

It includes:

- API
- Celery worker
- Celery beat
- Redis
- MLflow
- Airflow DB
- Airflow init
- Airflow scheduler
- Airflow webserver

Current local stability settings include:

- explicit DNS for API and worker containers
- reduced Celery worker concurrency
- reduced Airflow webserver workers
- reduced Airflow scheduler parsing processes

### One-time Airflow setup (local/prod-like)

Configure connection/variables through Airflow (or a secrets backend), not in compose:

```bash
airflow connections add 'opssight_api' \
  --conn-type 'http' \
  --conn-host 'api' \
  --conn-port '8000' \
  --conn-login '<workspace_user_email>' \
  --conn-password '<workspace_user_password>'
```

Optional scheduled-pipeline model default:

```bash
airflow variables set opssight_model_name '<model_name>'
```

Manual development run examples:

```bash
airflow dags trigger opssight_daily_pipeline --conf '{"model_id": 1, "input_path": "/opt/airflow/data/incoming.csv"}'
```

```bash
airflow dags trigger opssight_daily_pipeline --conf '{"model_name": "spotify-kmeans-recommender", "input_path": "/opt/airflow/data/incoming.csv"}'
```

With a custom input file:

```bash
airflow dags trigger opssight_daily_pipeline --conf '{"model_name": "spotify-kmeans-recommender", "input_path": "/opt/airflow/data/bad_drift_quality_with_mood.csv"}'
```

With schema-based model matching:

```bash
airflow dags trigger opssight_daily_pipeline --conf '{"input_path": "/opt/airflow/data/schema_validation_mood.csv"}'
```

### Development vs production configuration

In development, it is acceptable to trigger the DAG manually from the Airflow UI and paste a JSON config. This lets one local Airflow deployment test multiple OpsSight models without editing `.env`.

In production, each scheduled pipeline should get model context from one of these safer places:

- DAG trigger config generated by the upstream orchestration system
- Airflow Variables for a dedicated scheduled DAG
- Airflow Connection extras
- a secrets backend

Do not use root `.env` variables for per-customer model id/name. A single global `.env` value would make every DAG run target the same model and would break multi-tenant production behavior.

### User credential handling

For local development, the Airflow connection can use a workspace user's email/password.

For production, prefer a service identity or short-lived token flow:

- create a dedicated OpsSight service account per tenant or workspace
- restrict it to required ingestion permissions
- store credentials in Airflow Connections or a secrets backend
- rotate credentials periodically
- avoid embedding JWTs in DAG files or Docker Compose

The current login/password path verifies credentials by calling OpsSight `/auth/login`, then uses the returned access token for the validation request.

Recommended environment variables (inject from secret manager / CI):

- `AIRFLOW_CONN_OPSSIGHT_API`
- `AIRFLOW_VAR_OPSSIGHT_API_URL`
- `AIRFLOW_ADMIN_USERNAME`, `AIRFLOW_ADMIN_PASSWORD`, `AIRFLOW_ADMIN_EMAIL`
- `AIRFLOW_FERNET_KEY`, `AIRFLOW_WEBSERVER_SECRET_KEY`

---

## Operational Expectations

### If the quality gate fails

- run status becomes `failed`
- prediction and drift are skipped
- RCA is still queued

### If the quality gate passes

- accepted cleaned data is saved
- prediction can run
- drift can run
- incidents can be grouped and published live
- RCA is queued

---

## Related Files

- `backend/fastapi/app/tasks/ai_tasks.py`
- `backend/fastapi/app/tasks/remediation_tasks.py`
- `backend/fastapi/app/tasks/scheduler_tasks.py`
- `backend/fastapi/app/core/celery_app.py`
- `airflow-setup/dags/opssight_pipeline_dag.py`
- `docker-compose.yml`
