# Database Schema

PipelineDoctor uses PostgreSQL with schema-based multi-tenancy.

There are two layers:

- `public` schema for shared identity and integration metadata
- one tenant schema per workspace for monitoring and incident data

---

## Public Schema

### `users`

Cross-workspace user identities.

Important fields:

- `email`
- `hashed_password`
- `tenant_id`
- `role`
- `is_verified`
- `invite_token`
- `invite_accepted`

### `tenants`

Workspace registry.

Important fields:

- `id`
- `name`
- `schema_name`

### `slack_workspaces`

One Slack installation per tenant.

Important fields:

- `tenant_id`
- `slack_team_id`
- `slack_team_name`
- `bot_token`
- `bot_user_id`
- `scope`
- `connected_by_user_id`

### `slack_channels`

Saved default or known Slack channels for a workspace connection.

Important fields:

- `workspace_id`
- `slack_channel_id`
- `slack_channel_name`
- `is_default`

---

## Tenant Schema Tables

Each tenant schema contains the operational monitoring tables for that workspace.

### `ml_models`

Registered monitored models.

Important fields:

- `name`
- `version`
- `framework`
- `mlflow_model_name`
- `mlflow_alias`
- `mlflow_tracking_uri`
- `expected_features`

### `baselines`

Approved or draft reference datasets used for quality and drift.

Important fields:

- `model_id`
- `version`
- `schema`
- `profile`
- `status`
- `is_active`
- `file_path`

### `pipeline_runs`

One record per validation pipeline execution.

Important fields:

- `model_id`
- `baseline_version`
- `status`
- `file_path`
- `cleaned_data_path`
- `schema_changed`
- `created_at`

Current status values used by the pipeline are:

- `running`
- `success`
- `failed`

Note:

- the accepted cleaned dataset path is stored in DB
- the quarantine path is currently file-based output, not a separate DB column

### `schema_change_events`

Tracks extra or missing columns against the active baseline.

Important fields:

- `pipeline_run_id`
- `baseline_id`
- `new_columns`
- `missing_columns`
- `status`

### `data_quality_findings`

Raw quality findings captured from the incoming batch.

Important fields:

- `model_id`
- `pipeline_run_id`
- `column_name`
- `check_type`
- `success`
- `details`
- `created_at`

`pipeline_run_id` is a foreign key to `pipeline_runs.id`; this keeps raw quality findings tied to the validation run that produced them.

### `prediction_logs`

Saved model predictions for a run.

Important fields:

- `run_id`
- `input_data`
- `prediction`
- `created_at`

### `drift_findings`

Per-feature drift records.

Important fields:

- `run_id`
- `feature_name`
- `psi_score`
- `ks_score`
- `ks_pvalue`
- `drift_score`
- `drift_detected`
- `severity`

### `incident_groups`

Run-level alert grouping.

Important fields:

- `run_id`
- `title`
- `summary`
- `severity`
- `status`
- `primary_incident_id`

This is what keeps the incident list centered on one top-level alert per run.

### `incidents`

Detailed underlying incidents and RCA entries.

Important fields:

- `run_id`
- `group_id`
- `title`
- `description`
- `failure_type`
- `finding_type`
- `finding_id`
- `severity`
- `status`

### `agent_runs`

One doctor RCA execution per monitored run when queued.

### `agent_step_logs`

Persisted RCA trace steps for:

- detection
- reasoning
- parser
- reporting

### `remediation_runs`

Approved, blocked, staged, or deployed remediation executions tied to incidents.

Important fields:

- `incident_id`
- `run_id`
- `tenant_id`
- `action_type`
- `status`
- `trigger_mode`
- `created_by`
- `result_summary`
- `started_at`
- `finished_at`

Common statuses:

- `queued`
- `running`
- `cancel_requested`
- `canceled`
- `failed`
- `blocked`
- `rejected`
- `pending_promotion`
- `staged`
- `promotion_rejected`
- `deployed`

Older local data may contain `promoted` from the earlier single-step promotion flow.

### `remediation_action_logs`

Per-step remediation execution log.

Important fields:

- `remediation_run_id`
- `step_name`
- `status`
- `message`
- `payload`
- `created_at`

Important payloads:

- candidate result: `candidate_model_uri`, `candidate_mlflow_run_id`, `metrics`, `feature_columns`
- staging result: `staged_model_uri`, `staged_model_version`, `staged_alias`
- deployment result: `deployed_model_uri`, `deployed_alias`, `deployment_status`

### `incident_reports`

Versioned production reports for an incident.

Important fields:

- `incident_id`
- `pipeline_run_id`
- `model_id`
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
- `evidence_hash`
- `created_at`

The first report version is created after RCA completes. Later remediation events can create newer versions when a candidate is created, staged, rejected, or deployed.

---

## Provisioning and Repair Notes

- new workspaces create a dedicated tenant schema
- required tenant tables are created in that schema
- startup repair can backfill older half-created tenant schemas
- request middleware sets `search_path` to `<tenant_schema>, public`

---

## Relationship Overview

```text
public.users -------------------- public.tenants
        |                                |
        |                                +-- public.slack_workspaces -- public.slack_channels
        |
tenant.ml_models -------- tenant.baselines
        |
        +-- tenant.pipeline_runs
              |
              +-- tenant.data_quality_findings
              +-- tenant.prediction_logs
              +-- tenant.drift_findings
              +-- tenant.schema_change_events
              +-- tenant.incident_groups -- tenant.incidents
              |                                |
              |                                +-- tenant.remediation_runs -- tenant.remediation_action_logs
              |                                +-- tenant.incident_reports
              |
              +-- tenant.agent_runs -- tenant.agent_step_logs
```
