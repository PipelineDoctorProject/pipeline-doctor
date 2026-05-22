# API Reference

Base URL: `http://127.0.0.1:8000`  
Interactive Docs: `http://127.0.0.1:8000/docs`

All protected endpoints require a Bearer JWT token in the `Authorization` header.

---

## Auth

### `POST /auth/signup`

Register a new user account and send OTP.

### `POST /auth/verify-otp`

Verify OTP and return JWT tokens.

### `POST /auth/login`

Login with email and password.

**Response**

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

### `POST /auth/refresh`

Refresh the access token from a valid refresh token.

---

## ML Models

### `POST /ml-models/`

Register a new model from MLflow metadata.

### `GET /ml-models/`

List registered models.

---

## Baselines

### `POST /baseline/upload?model_id=<id>`

Upload a CSV to create a baseline.

---

## Pipeline Runs

### `GET /runs/`

List pipeline runs.

### `GET /runs/{run_id}/download-cleaned`

Download the cleaned CSV for a specific run.

---

## Data Quality

### `GET /data-quality/`

List stored data quality findings.

Optional query params:

- `model_id`

### `POST /data-quality/validate?model_id=<id>`

Upload a CSV and run validation for a specific model.

### `POST /data-quality/validate-auto`

Upload a CSV and let the backend infer the matching active model from the schema.

### `GET /data-quality/explain?run_id=<run_id>`

Return the explanation layer for a specific run.

This endpoint does not decide whether checks passed or failed. It summarizes stored failed findings into:

- `summary`
- `Why This Matters`
- `Suggested Remediation`

---

## Drift Findings

### `GET /drift-findings/`

List stored drift findings.

Optional query params:

- `model_id`
- `run_id`

### `POST /drift-findings/backfill/{run_id}`

Backfill drift findings for an existing run if they do not already exist.

### `GET /drift-findings/explain?run_id=<run_id>`

Return the explanation layer for a specific run.

This endpoint does not decide whether drift exists. It explains stored findings using:

- `summary`
- `Possible Business Interpretation`
- `What Changed Compared To Baseline`

---

## Incidents

### `GET /incidents/`

List stored incidents.

### `GET /incidents/{incident_id}/agent-runs`

List agent runs for one incident.

### `GET /incidents/agent-runs/{agent_run_id}/steps`

List stored step logs for an agent run.

---

## WebSockets

### `WS /ws/agent-trace/{run_id}`

Live RCA execution trace for the incident drawer.

### `WS /ws/incidents`

Live incident feed for automatic incident page refresh.

---

## Health

### `GET /health`

Basic API health check.

### `GET /health/celery`

Celery and scheduler health status.
