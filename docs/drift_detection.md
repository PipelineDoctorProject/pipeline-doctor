# Drift Detection

The Drift Detection layer only runs after the accepted cleaned dataset passes the post-clean quality gate.

Its job is to answer:

- has the current production batch shifted away from the baseline population?
- did the model-output behavior also shift?

There are two monitored categories:

1. data drift on input features
2. concept drift on model output

---

## Execution Flow

```text
Accepted cleaned CSV
    |
run_drift_checks(...)
    |
data drift per comparable feature
concept drift on prediction output when available
    |
store drift findings
    |
create detailed incidents
    |
group incidents by run
```

If the quality gate fails, this stage is skipped entirely.

---

## Main Metrics

### PSI

Population Stability Index compares the baseline distribution with the current batch distribution.

Typical interpretation:

| PSI | Meaning |
|---|---|
| `< 0.1` | stable |
| `0.1 - 0.2` | monitor |
| `0.2 - 0.3` | warning |
| `0.3 - 0.5` | significant drift |
| `>= 0.5` | major drift |

### KS

The Kolmogorov-Smirnov test compares the shape of the cumulative distributions.

Stored values include:

- `ks_score`
- `ks_pvalue`

### Final drift score

The stored drift score is:

```python
drift_score = max(psi_score, ks_score)
```

---

## Severity

Current severity mapping:

| Drift score | Severity |
|---|---|
| `< 0.2` | low |
| `0.2 - 0.3` | medium |
| `0.3 - 0.5` | high |
| `>= 0.5` | critical |

---

## Baseline Inputs

The drift layer prefers a raw baseline CSV when available.

If the raw baseline file is missing or incompatible, the system falls back to profile-based comparison using the active baseline profile.

---

## Incident Behavior

- detailed drift incidents are still created as evidence
- top-level incident listing is grouped by run through `incident_groups`
- Slack is centered on the primary run-level alert, not every individual drift finding

---

## AI Explanation Layer

The Drift page explanation endpoint summarizes stored findings but does not override the underlying metrics.

Endpoint:

`GET /drift-findings/explain?run_id=<run_id>`

Product rule:

- metrics detect
- AI explains

---

## Related Files

- `backend/fastapi/app/services/drift/drift_service.py`
- `backend/fastapi/app/services/drift/storage.py`
- `backend/fastapi/app/services/drift/utils.py`
- `backend/fastapi/app/api/routes/drift_findings.py`
