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

1. locates an input CSV
2. logs into the OpsSight API
3. sends the file to `/data-quality/validate?model_id=...`

### Airflow auth rule

Use application credentials:

- `OPSSIGHT_API_EMAIL`
- `OPSSIGHT_API_PASSWORD`

Do not use the Airflow UI login for API calls.

### Access token rule

Do not hardcode a long-lived API access token in Airflow.

The DAG should:

1. call `POST /auth/login`
2. read the returned `access_token`
3. call the validation endpoint

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
