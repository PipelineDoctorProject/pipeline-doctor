# API Reference

Base URL: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

Protected endpoints expect a bearer token in the `Authorization` header.

---

## Auth and Onboarding

### `POST /auth/signup`

Create a new user and send OTP.

### `POST /auth/verify-otp`

Verify OTP and return:

- `access_token`
- `refresh_token`
- `token_type`
- `onboarding_required`

### `POST /auth/login`

Login with email and password.

### `POST /auth/refresh`

Refresh the access token from the refresh cookie.

### `POST /auth/logout`

Clear auth cookies.

### `GET /dashboard/me`

Return the authenticated user's current dashboard context.

This is the endpoint to use when scripts need the current user's workspace and tenant id. The project does not expose `GET /auth/me`.

Important response fields include:

- user identity
- role
- workspace metadata
- `workspace.tenant_id`

### `POST /onboarding/company`

Create the workspace after OTP verification.

Returns:

- `tenant_id`
- `workspace_name`
- `schema_name`
- refreshed auth tokens

### `POST /invite/member`

Admin-only member invitation.

### `POST /invite/accept`

Accept member invite and set password.

### `DELETE /tenant/{tenant_id}`

Admin-only tenant deletion for local reset and controlled cleanup.

Use this carefully. In local development, first call `GET /dashboard/me` to find the current `workspace.tenant_id`, then call this endpoint with the same access token.

---

## Models and Baselines

### `GET /ml-models/`

List tenant-visible models.

### `POST /ml-models/`

Register a model.

### `POST /baseline/upload?model_id=<id>`

Upload a baseline CSV for a model.

---

## Pipeline Runs

### `GET /runs/`

List pipeline runs.

### `GET /runs/{run_id}/download-cleaned`

Download the accepted cleaned CSV for a run.

---

## Data Quality

### `GET /data-quality/`

List stored data-quality findings.

Optional query params:

- `model_id`

### `POST /data-quality/validate?model_id=<id>`

Upload a CSV and run the full quality pipeline for a specific model.

Important response fields now include:

- `pipeline_status`
- `cleaned_data_path`
- `quarantine_data_path`
- `result` (raw findings)
- `post_clean_validation`
- `cleaning_report`
- `quality_gate`
- `prediction_status`
- `drift_status`
- `root_cause_analysis`

### `POST /data-quality/validate-auto`

Upload a CSV and let the backend infer the best active model from schema overlap.

### `GET /data-quality/explain?run_id=<run_id>`

Explain stored failed data-quality findings.

---

## Drift

### `GET /drift-findings/`

List stored drift findings.

Optional query params:

- `model_id`
- `run_id`

### `POST /drift-findings/backfill/{run_id}`

Backfill drift for an existing run if needed.

### `GET /drift-findings/explain?run_id=<run_id>`

Explain stored drift findings.

---

## Incidents

### `GET /incidents/`

List grouped top-level incidents, one representative alert per run-level group.

Optional query params:

- `model_id`

### `GET /incidents/filtered`

Same grouped incident view, kept for frontend compatibility.

### `POST /incidents/`

Create a manual incident.

### `GET /incidents/{incident_id}`

Get one incident.

### `GET /incidents/{incident_id}/children`

Get all incidents inside the same `incident_group`.

### `GET /incidents/{incident_id}/agent-runs`

Get RCA agent runs for the incident's run.

### `GET /incidents/agent-runs/{agent_run_id}/steps`

Get stored RCA step logs.

---

## Remediation

### `GET /remediation/incident/{incident_id}`

List remediation runs for an incident.

### `GET /remediation/incident/{incident_id}/context`

Return remediation context for the incident drawer, including:

- expected features
- dataset columns
- target candidates
- suggested target column
- readiness warnings

### `POST /remediation/incident/{incident_id}/approve?target_column=<name>`

Admin-only remediation approval.

Current approval rules depend on:

- user role
- incident severity
- remediation policy
- cleaned data availability
- configured `expected_features`
- valid target column

For unsupervised models, `target_column` can be omitted when the remediation context marks `target_required=false`.

### `POST /remediation/{remediation_run_id}/reject`

Admin-only rejection for a pending/active remediation run.

If the run is already `pending_promotion` or `staged`, this rejects the candidate instead of canceling execution.

### `POST /remediation/{remediation_run_id}/promote?review_notes=<text>`

Admin-only candidate staging.

Despite the historical endpoint name, the production behavior is staging:

- creates an MLflow registered model version from the candidate artifact
- points the configured staging alias, usually `staging`, at that version
- records staged metadata in `remediation_action_logs`
- moves the remediation run to `staged`

This endpoint must not update the live `champion` alias.

### `POST /remediation/{remediation_run_id}/confirm-deployment?deployment_notes=<text>`

Admin-only deployment confirmation.

Use this only after the external deployment pipeline has deployed the MLflow staging alias and serving checks have passed.

This endpoint:

- points the configured champion alias, usually `champion`, at the staged version
- updates the OpsSight model record
- records deployment metadata
- moves the remediation run to `deployed`

### `GET /remediation/{remediation_run_id}`

Get one remediation run.

### `GET /remediation/{remediation_run_id}/logs`

Get remediation action logs.

---

## Reports

### `GET /reports/incidents/{incident_id}`

List all report versions for an incident.

Reports are versioned because the incident story changes over time. RCA creates the initial report, and remediation lifecycle changes can create newer versions.

### `GET /reports/incidents/{incident_id}/latest`

Return the latest production report for an incident.

The frontend uses this to open the PDF-style report page from the incident drawer.

### `GET /reports/{report_id}`

Return a specific report version.

Important report fields include:

- `version`
- `status`
- `severity`
- `summary`
- `executive_narrative`
- `root_cause`
- `key_findings`
- `remediation`
- `model_context`
- `next_actions`
- `timeline`

---

## Slack

### `GET /slack/connect`

Create an OAuth connect URL for the current admin workspace.

### `GET /slack/callback`

OAuth callback handler.

### `GET /slack/status`

Return Slack connection state, default channel, and delivery-readiness info.

### `GET /slack/channels`

List Slack channels for the connected workspace.

### `PUT /slack/default-channel`

Save the default incident-alert channel.

### `DELETE /slack/disconnect`

Disconnect the current workspace from Slack.

---

## WebSockets

### `WS /ws/agent-trace/{run_id}`

Live RCA step updates for one run.

### `WS /ws/incidents`

Live incident feed used for grouped incident refresh and navbar notifications.

Common event payload:

```json
{
  "event": "incident_created",
  "incident": {
    "id": 1,
    "pipeline_run_id": 10,
    "severity": "high",
    "status": "open"
  }
}
```

Frontend behavior:

- ignores heartbeat frames such as `connected` and `ping`
- refetches tenant-scoped incidents before rendering details
- updates the incident list, drawer context, navbar unread count, and notification dropdown

Production note: REST refetches are tenant-protected, but the WebSocket transport should also be tenant-authenticated and tenant-scoped before public multi-tenant deployment.

---

## Health

### `GET /health`

Basic API health check.

### `GET /health/celery`

Worker and beat health check.
