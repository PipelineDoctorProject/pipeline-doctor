# Model Lifecycle

This document explains how OpsSight handles production model lifecycle from monitoring to remediation candidate, staging, deployment confirmation, and future monitoring.

---

## Core Principle

OpsSight should not silently replace a production model.

The safe production contract is:

```text
Detect -> Explain -> Recommend -> Approve -> Create Candidate -> Stage -> Deploy Externally -> Confirm -> Monitor
```

This protects production systems from accidental automatic deployment while still making remediation fast and auditable.

---

## Main Actors

| Actor | Responsibility |
|---|---|
| OpsSight | Detect incidents, explain evidence, run approved remediation, log candidates, track lifecycle |
| Admin user | Approve remediation, stage/reject candidates, confirm deployment |
| MLflow | Store candidate artifacts, registered model versions, and aliases |
| Customer CI/CD | Deploy staged model to serving infrastructure |
| Serving platform | Hosts the actual production model endpoint |
| Airflow/customer pipeline | Sends production batch data to OpsSight for monitoring |

---

## Lifecycle States

### 1. Champion

`champion` is the currently live model version.

OpsSight uses champion for:

- prediction
- monitoring context
- active model metadata
- remediation source model reference

Example:

```text
models:/spotify-kmeans-recommender@champion
```

### 2. Candidate

A candidate is produced by remediation retraining or an external training workflow.

Candidate URI:

```text
runs:/<run_id>/candidate_model
```

A candidate is not registered as live and is not production traffic-ready by default.

### 3. Staging

Staging means the candidate passed human review and is ready for deployment validation.

OpsSight sets:

```text
models:/<model_name>@staging
```

Staging does not mean the model is serving production traffic.

### 4. Deployed Champion

Deployment confirmation means the staged model has been deployed by the external serving system and passed checks. Only then should OpsSight update:

```text
models:/<model_name>@champion
```

---

## Full Flow From Incident

```text
1. Pipeline run creates severe findings
2. OpsSight creates an incident group
3. RCA explains likely root cause
4. Remediation panel recommends action
5. Admin approves retraining
6. Celery worker prepares data and trains/refits candidate
7. Candidate model is logged to MLflow
8. Remediation run status becomes pending_promotion
9. Admin reviews candidate metrics and MLflow artifacts
10. Admin clicks Stage candidate
11. MLflow staging alias points to candidate version
12. Customer deployment pipeline deploys staging
13. Admin confirms deployment after smoke tests
14. MLflow champion alias points to deployed version
15. OpsSight model metadata is updated
16. Future pipeline runs monitor the new champion
```

---

## What Happens on Each Button

### Approve retraining

Creates a `remediation_run`, queues Celery, and starts the worker.

Does not:

- register a new live MLflow version
- update `champion`
- update live model metadata

### Stage candidate

Creates an MLflow registered model version from the candidate artifact and points the `staging` alias to it.

Does not:

- update `champion`
- update the serving endpoint
- mark the model live

### Reject candidate

Marks the candidate as rejected.

Does not:

- delete the MLflow run
- update `staging`
- update `champion`

### Confirm deployment

Confirms that the staged model has actually been deployed externally and passed checks. This updates:

- MLflow `champion` alias
- OpsSight model version
- OpsSight model alias
- OpsSight model run id
- expected features when safe

---

## Recommended CI/CD Integration

In production, customer deployment automation should watch for one of these:

- MLflow `staging` alias update
- OpsSight webhook/event in future versions
- manual deployment trigger from a release system
- scheduled deployment job that checks staged versions

The deployment pipeline should:

1. Resolve `models:/<model_name>@staging`.
2. Deploy it to a non-production or canary target.
3. Run smoke tests.
4. Compare basic predictions/cluster output.
5. Verify service health.
6. Promote to production serving.
7. Call OpsSight deployment confirmation or ask an admin to confirm in the UI.

---

## Rollback Strategy

Because `champion` is an MLflow alias, rollback can be alias-based:

1. Identify previous champion version.
2. Reassign `champion` to the previous version.
3. Update serving system to load the previous champion.
4. Add an incident/remediation log note.
5. Re-run monitoring on the rollback batch.

OpsSight should eventually expose rollback as an admin-only operation, but manual MLflow alias rollback is acceptable in local development.

---

## Safety Checks Before Confirming Deployment

Before clicking `Confirm deployment`, verify:

- candidate MLflow run exists
- model artifact loads
- expected features match serving input contract
- schema changes were approved if feature columns changed
- metrics are acceptable for the model type
- serving endpoint loaded the staged model
- smoke tests passed
- fallback/rollback path is known

---

## Development Testing Checklist

For a local end-to-end test:

1. Register or bootstrap a local MLflow source model.
2. Make sure it has a `champion` alias.
3. Register the model in OpsSight.
4. Trigger Airflow DAG with a bad/drifted dataset.
5. Open the created incident group.
6. Approve remediation.
7. Wait for `pending_promotion`.
8. Open the candidate run in MLflow.
9. Click `Stage candidate`.
10. Verify MLflow registered model has `staging`.
11. Click `Confirm deployment`.
12. Verify MLflow registered model has `champion`.
13. Trigger a new DAG run and confirm OpsSight monitors the champion version.

---

## Related Docs

- [remediation.md](./remediation.md)
- [ml_integration.md](./ml_integration.md)
- [automation_and_scheduler.md](./automation_and_scheduler.md)
- [api_reference.md](./api_reference.md)
