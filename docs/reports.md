# Production Reports

OpsSight reports are the durable, user-facing record of what happened during an incident and what happened after remediation. The report is designed to read like a production incident document: executive summary, root cause, evidence, remediation state, model/run context, timeline, and next actions.

---

## Purpose

The report system exists so users do not need to reconstruct the incident from raw logs.

It should answer:

- what failed or became risky
- which evidence supports that conclusion
- what the RCA agent recommended
- whether remediation was approved, rejected, staged, or deployed
- which model version or alias changed
- what the operator should do next

---

## Report Lifecycle

```text
Pipeline run creates findings
    |
Incident group is created
    |
Doctor RCA task runs Detection -> AI Reasoning -> Parsing -> Reporting
    |
Initial incident report version is saved
    |
Remediation state changes
    |
New report versions are created with updated remediation state
    |
User opens Full Report from the incident drawer
```

The key production rule is:

**RCA creates the first report, and remediation updates the report as the lifecycle progresses.**

That means the report should not stop at root cause. It should also reflect later states such as `queued_for_execution`, `candidate_ready_for_review`, `candidate_staged_for_deployment`, `remediation_deployed`, or `candidate_rejected`.

---

## Report Versioning

Reports are stored in `incident_reports`.

Each important lifecycle update can create a new report version. The latest version is what the UI shows by default.

Examples:

| Version | Example status | Meaning |
|---|---|---|
| `v1` | `awaiting_approval` | RCA completed and remediation is waiting for admin approval. |
| `v2` | `candidate_ready_for_review` | Approved remediation produced an MLflow candidate. |
| `v3` | `candidate_staged_for_deployment` | Admin staged the candidate under the MLflow staging alias. |
| `v4` | `remediation_deployed` | Deployment was confirmed and champion alias was updated. |

Older versions remain useful as audit history.

---

## UI Flow

From the incident drawer:

1. Open the incident group.
2. Review the RCA card.
3. Click `Full Report`.
4. Read the production-style report page.
5. Use `Download PDF` to print/save the report as a PDF.

The report page is intentionally browser-print based in the current implementation. This keeps the local/dev flow simple while still producing a PDF-like deliverable. A future production deployment can replace this with server-side PDF rendering if strict formatting, signatures, or archival policies are required.

---

## Report Content

The report page includes:

- report title and version
- generated time
- severity
- run id
- RCA source/provider
- report status
- executive narrative
- root-cause analysis
- key findings and affected columns
- remediation state
- candidate/staged/deployed model URIs when available
- model and run context
- next actions
- evidence hash

The evidence hash is used to make it easier to prove which evidence set produced the report.

---

## Remediation-Aware Statuses

The report can reflect these remediation statuses:

| Report status | Meaning |
|---|---|
| `manual_action_required` | The system recommends human investigation before any model/baseline change. |
| `awaiting_approval` | Remediation is possible but waiting for admin approval. |
| `queued_for_execution` | Admin approved remediation and Celery has queued it. |
| `remediation_running` | Approved remediation is executing. |
| `candidate_ready_for_review` | Candidate retraining completed and needs review. |
| `candidate_staged_for_deployment` | Candidate was staged in MLflow, usually as `@staging`. |
| `remediation_deployed` | Deployment was confirmed and `@champion` was updated. |
| `candidate_rejected` | Candidate was rejected and live model remains unchanged. |
| `remediation_failed` | Remediation failed before producing or promoting a candidate. |

---

## LLM Usage

The LLM is used for RCA reasoning and narrative generation, but OpsSight should keep monitoring evidence as the source of truth.

Production safety rules:

- The LLM should explain evidence, not invent missing evidence.
- Parsed severity should not undercut the highest detected signal severity.
- Reports should include structured evidence and machine-readable remediation state.
- If the LLM is unavailable, deterministic fallback reporting should still produce a useful report.

---

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /reports/incidents/{incident_id}` | List report versions for an incident. |
| `GET /reports/incidents/{incident_id}/latest` | Fetch the latest report version. |
| `GET /reports/{report_id}` | Fetch a specific report version. |

All report endpoints are tenant-protected. A user can only read reports for incidents that belong to models in their tenant.

---

## Related Code

- `backend/fastapi/app/api/routes/reports.py`
- `backend/fastapi/app/models/incident_report.py`
- `backend/fastapi/app/services/incidents/report_builder.py`
- `backend/fastapi/app/services/incidents/report_service.py`
- `backend/fastapi/app/services/remediation/reporting.py`
- `frontend/src/pages/reports/IncidentReportPage.jsx`
- `frontend/src/store/reportStore.js`

---

## Related Docs

- [ai_orchestration.md](./ai_orchestration.md)
- [remediation.md](./remediation.md)
- [model_lifecycle.md](./model_lifecycle.md)
- [api_reference.md](./api_reference.md)
