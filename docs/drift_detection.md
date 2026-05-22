# Drift Detection

The Drift Detection layer runs after validation and cleaned-data generation. Its job is to answer:

**Has the current production batch shifted away from the baseline population?**

There are two monitored categories:

1. data drift on input features
2. concept drift on prediction output

---

## Execution Flow

```text
Cleaned CSV
    |
run_drift_checks(...)
    |
Data drift per feature
Concept drift on predictions
    |
Store drift findings
    |
Create incidents for high/critical signals
```

---

## Main Metrics

### PSI

**File:** `backend/fastapi/app/services/drift/metrics.py`

Population Stability Index compares the baseline distribution with the current batch distribution.

Typical interpretation:

| PSI | Meaning |
|---|---|
| `< 0.1` | stable |
| `0.1 - 0.2` | monitor |
| `0.2 - 0.3` | warning |
| `0.3 - 0.5` | significant drift |
| `> 0.5` | major drift |

### KS

Also computed in `metrics.py`, the Kolmogorov-Smirnov test compares the shape of the cumulative distributions.

The result includes:

- `ks_score`
- `ks_pvalue`

### Final drift score

The stored `drift_score` is the maximum of PSI and KS:

```python
drift_score = max(psi_score, ks_score)
```

---

## Concept Drift

**File:** `backend/fastapi/app/services/drift/concept_drift.py`

Concept drift is based on prediction behavior rather than only input features.

It compares:

- baseline prediction distribution
- current run prediction distribution

This catches cases where the model output changes even when the feature inputs look relatively normal.

---

## Severity and Incidents

**File:** `backend/fastapi/app/services/drift/utils.py`

| Drift score | Severity |
|---|---|
| `< 0.2` | low |
| `0.2 - 0.3` | medium |
| `0.3 - 0.5` | high |
| `>= 0.5` | critical |

High and critical drift findings can create incidents that later appear in the Incidents page and feed the RCA pipeline.

---

## Stored Findings

Each row in `drift_findings` contains:

- `run_id`
- `feature_name`
- `psi_score`
- `ks_score`
- `ks_pvalue`
- `drift_score`
- `drift_detected`
- `severity`
- `created_at`

These stored values are the source of truth for the Drift page.

---

## AI Explanation Layer

The Drift page now includes an optional explanation layer for a selected run.

### What it does

It does not detect drift or override severity.

Instead, it explains:

- `Possible Business Interpretation`
- `What Changed Compared To Baseline`

### Endpoint

`GET /drift-findings/explain?run_id=<run_id>`

### Behavior

- if a live LLM is configured, the backend summarizes the stored drift findings into business-friendly language
- if no LLM is available, the backend returns a structured deterministic explanation
- the metric table, PSI, KS, and drift score remain the source of truth

This follows the same product rule as Data Quality:

- metrics detect
- AI explains

---

## Related Files

- `backend/fastapi/app/api/routes/drift_findings.py`
- `backend/fastapi/app/services/drift/drift_service.py`
- `backend/fastapi/app/services/drift/metrics.py`
- `backend/fastapi/app/services/ai_explanations/insight_explainer.py`
- `frontend/src/pages/drift/DriftPage.jsx`
