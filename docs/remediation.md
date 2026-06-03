# Remediation and Approval

Remediation is the controlled operational path from an incident to a proposed fix. In OpsSight, remediation is intentionally not a silent automatic replacement of the production model. It is an auditable workflow with approval, execution logs, candidate review, staging, and deployment confirmation.

---

## Goals

The remediation system is designed to:

- show the recommended remediation path inside the incident drawer
- require admin approval before executing risky actions
- persist every remediation attempt
- show worker execution logs in the UI
- create candidate models without mutating the live champion model
- let admins stage or reject candidates
- require a separate deployment confirmation before the champion alias changes

---

## High-Level Flow

```text
Incident group opens in the Incidents page
    |
RCA and policy engine recommend a remediation mode
    |
Admin approves remediation
    |
Celery worker executes remediation
    |
Candidate model is logged to MLflow
    |
Run becomes pending_promotion
    |
Admin reviews metrics and artifacts
    |
    +-- reject candidate
    |       |
    |       +-- run becomes promotion_rejected
    |       +-- live model remains unchanged
    |
    +-- stage candidate
            |
            +-- MLflow staging alias points to candidate version
            +-- run becomes staged
            +-- live champion remains unchanged
            |
            +-- external deployment pipeline deploys staging
                    |
                    +-- admin confirms deployment
                            |
                            +-- MLflow champion alias is updated
                            +-- OpsSight model record is updated
                            +-- run becomes deployed
```

---

## Remediation Statuses

| Status | Meaning | Terminal? |
|---|---|---|
| `queued` | Admin approved the remediation and the worker task was queued. | No |
| `running` | Celery worker is executing the remediation. | No |
| `cancel_requested` | Admin requested cancellation while the worker is running. | No |
| `canceled` | Worker observed cancellation and stopped safely. | Yes |
| `failed` | Worker failed before producing a usable candidate. | Yes |
| `blocked` | Policy or readiness checks blocked execution. | Yes |
| `rejected` | Admin rejected remediation before execution. | Yes |
| `pending_promotion` | Candidate retraining completed and waits for human review. | No |
| `staged` | Candidate was registered and assigned the MLflow `staging` alias. | No |
| `promotion_rejected` | Candidate was reviewed and rejected. | Yes |
| `deployed` | Deployment was confirmed and MLflow `champion` alias was updated. | Yes |

Older records may contain `promoted` from the previous single-step flow. New production-style runs should use `staged` followed by `deployed`.

---

## Admin Approval Rules

Approval is allowed only when:

- the logged-in user is an admin
- the incident belongs to the current tenant
- the incident has a remediation recommendation that policy allows
- no active remediation run is already queued/running/staged for that incident
- cleaned data exists for the pipeline run
- the selected model belongs to the tenant
- usable feature columns can be resolved
- target rules are satisfied for supervised retraining
- unsupervised retraining is allowed only for supported clustering-style models

Approval is intentionally separate from deployment. Approving remediation only starts execution. It does not update the live model.

---

## Supervised vs Unsupervised Remediation

### Supervised models

A supervised model learns from features and a target label.

Examples:

- fraud classifier learns `is_fraud`
- churn model learns `churned`
- price model learns `sale_price`

For supervised retraining, OpsSight requires a target column because the model needs the correct answer during training.

Readiness checks include:

- target column exists
- target is not one of the feature columns
- target has at least two distinct values for classification-style tasks
- target is not entirely null
- enough clean rows exist
- expected feature columns can be found

### Unsupervised models

An unsupervised model learns patterns from features only.

Examples:

- KMeans clustering
- anomaly grouping
- segment discovery

For unsupervised remediation, no target column is required. OpsSight refits the estimator using the accepted feature columns from the cleaned dataset and baseline/model metadata.

For clustering, useful review metrics include:

- `cluster_count`
- `silhouette_score`
- selected feature columns
- cluster distribution
- sample assigned clusters

The platform still treats high-severity unsupervised incidents as risky. A high severity incident can trigger the recommendation, but the candidate must still be reviewed and staged by an admin.

---

## Candidate Creation

When remediation execution succeeds, the worker logs a candidate model to MLflow. This produces:

- `candidate_mlflow_run_id`
- `candidate_model_uri`
- metrics
- feature list
- source model metadata
- source pipeline run id

Example candidate URI:

```text
runs:/bb00b5d16c147088e9d7f8082568398/candidate_model
```

At this point:

- the live model is unchanged
- the candidate is not serving production traffic
- the incident drawer shows `Pending Promotion`
- the admin must inspect the MLflow run and OpsSight logs

---

## Stage Candidate

The `Stage candidate` action should:

- create or reuse the MLflow registered model
- create a new model version from the candidate artifact
- assign the MLflow `staging` alias to that version
- store staged metadata in remediation logs
- set the remediation run to `staged`

The staging action must not:

- update the OpsSight live model record to the new version
- update the MLflow `champion` alias
- claim production deployment has happened

This separation is important because OpsSight does not know whether the customer's serving system has actually deployed and validated the candidate.

---

## Confirm Deployment

The `Confirm deployment` action is the final human-verified step. It should be clicked only after:

- the deployment pipeline picked up the MLflow `staging` alias
- the serving endpoint deployed the candidate
- smoke tests passed
- health checks passed
- rollback risk was considered

Confirmation updates:

- MLflow `champion` alias
- OpsSight `MLModel.version`
- OpsSight `MLModel.mlflow_alias`
- OpsSight `MLModel.mlflow_run_id`
- expected feature list if the candidate has a validated feature list

After deployment confirmation, future monitoring should load:

```text
models:/<model_name>@champion
```

---

## Reject and Cancel Behavior

### Reject before execution

If a remediation run is queued or approved, admin rejection moves it to `rejected`.

### Cancel while running

If a remediation run is already running, admin rejection requests cancellation. The worker must check cancellation status before and after major stages. If cancellation is observed, the run becomes `canceled`.

### Reject candidate

If the run is `pending_promotion` or `staged`, rejection moves it to `promotion_rejected`. The live model remains unchanged.

---

## UI Flow

Inside the incident drawer:

1. Review RCA summary and recommended action.
2. Review remediation context.
3. If admin and allowed, click `Approve retraining`.
4. Wait for run history to show `Pending Promotion`.
5. Open the candidate in MLflow and inspect metrics/artifacts.
6. Click `Stage candidate` if acceptable.
7. Deploy the `staging` alias through the external deployment path.
8. Click `Confirm deployment` after serving validation.

The UI should show:

- latest run status
- action type
- execution mode
- readiness warnings
- model context
- feature setup
- candidate model URI
- staged model URI
- step-by-step remediation logs

---

## Important Tables

### `remediation_runs`

Stores one remediation attempt.

Important fields:

- `incident_id`
- `run_id`
- `tenant_id`
- `action_type`
- `trigger_mode`
- `status`
- `created_by`
- `result_summary`
- `started_at`
- `finished_at`

### `remediation_action_logs`

Stores each important step.

Typical steps:

- `approval`
- `start`
- `retraining`
- `staging_approval`
- `deployment_confirmation`
- `promotion_review`
- `failure`
- `canceled`

---

## Related Code

- `backend/fastapi/app/api/routes/remediation.py`
- `backend/fastapi/app/tasks/remediation_tasks.py`
- `backend/fastapi/app/services/remediation/retraining_service.py`
- `backend/fastapi/app/services/remediation/promotion_service.py`
- `backend/fastapi/app/services/remediation/reporting.py`
- `frontend/src/components/incidents/IncidentRemediationPanel.jsx`
- `frontend/src/store/remediationStore.js`

---

## Related Docs

- [model_lifecycle.md](./model_lifecycle.md)
- [ml_integration.md](./ml_integration.md)
- [data_quality.md](./data_quality.md)
- [schema_evolution.md](./schema_evolution.md)
- [automation_and_scheduler.md](./automation_and_scheduler.md)
- [api_reference.md](./api_reference.md)
