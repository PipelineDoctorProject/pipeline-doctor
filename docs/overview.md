# Current Sprint Overview

This sprint is now split into focused workstream docs instead of one long summary page.

---

## Main Goals

- move data cleaning from demo-style normalization to a production-style acceptance gate
- reduce alert noise by grouping incidents per run
- make remediation visible and actionable from the incident drawer
- harden onboarding, invite, and tenant-isolation flows
- make Slack delivery and realtime updates operationally reliable

---

## Workstream Docs

| File | Focus |
|---|---|
| [data_quality_workstream.md](./data_quality_workstream.md) | production cleaning gate, quarantine, and verified quality behavior |
| [incidents_and_realtime.md](./incidents_and_realtime.md) | incident grouping, live refresh, and drawer behavior |
| [remediation.md](./remediation.md) | approval flow, remediation runs, and retraining execution |
| [slack.md](./slack.md) | Slack OAuth, default-channel delivery, and alerting behavior |
| [auth_and_tenant.md](./auth_and_tenant.md) | onboarding, invites, member auth, and tenant isolation hardening |

---

## Shared Runtime Setup This Week

- API, worker, beat, Redis, MLflow, and Airflow run from the root `docker-compose.yml`
- frontend runs separately with Vite
- explicit DNS was added to API and worker containers
- MLflow allowed-hosts was widened for container-to-container access
- Celery worker concurrency was reduced for local stability
- Airflow webserver and scheduler were tuned down for local Docker reliability

---

## Remaining Production Gaps

- rotate `SECRET_KEY` to a real 32+ byte secret before deployment
- add end-to-end regression tests for signup, onboarding, invite, Slack, remediation, and validation gating
- decide whether cleaned and quarantined artifacts should move to object storage instead of only Docker volumes
- add a deployment smoke test that covers health, auth, Slack readiness, and one validation run
