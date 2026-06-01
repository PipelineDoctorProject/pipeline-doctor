# Current Sprint: Remediation

This workstream covers remediation visibility, approval, and background execution.

---

## Delivered

- remediation recommendation is included in RCA and final-report payloads
- the incident drawer now shows remediation context and admin actions
- admin users can approve or reject remediation from the UI
- remediation runs are persisted in `remediation_runs`
- action-level execution logs are persisted in `remediation_action_logs`
- scikit-learn retraining executes through the Celery worker path

---

## Current Approval Model

Approval is only allowed when:

- the user is an admin
- the incident is allowed by the remediation policy
- cleaned data exists for the run
- the model has `expected_features`
- the requested target column exists
- usable feature columns remain for retraining

---

## Current Runtime Behavior

- policy-blocked incidents remain visible but cannot be executed
- approved remediation creates a background remediation run
- worker execution logs step-by-step status into `remediation_action_logs`
- reject actions move the remediation run into a terminal `rejected` state

---

## Production Value

This turns remediation from an API-only capability into an auditable operational flow:

- recommendation
- approval or rejection
- worker execution
- step logs
- persisted outcome

---

## Related Docs

- [api_reference.md](./api_reference.md)
- [automation_and_scheduler.md](./automation_and_scheduler.md)
- [database_schema.md](./database_schema.md)
