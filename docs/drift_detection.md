# Drift Detection

The Drift Detection layer runs after the Data Quality checks and ML predictions. Its job is to answer: **"Has the real-world data shifted away from what the model was trained on?"**

There are two types of drift monitored:
1. **Data Drift** — Did the input features change?
2. **Concept Drift** — Did the model's output pattern change?

---

## 🔄 Execution Flow

```
Cleaned CSV (from Data Quality Layer)
        ↓
drift_service.py → run_drift_checks()
        ↓
  ┌─────────────────────┐
  │ 1. Data Drift       │ ← data_drift.py   → PSI + KS per feature
  │ 2. Concept Drift    │ ← concept_drift.py → PSI + KS on predictions
  └─────────────────────┘
        ↓
save_drift_finding_and_incident()
        ↓
drift_findings table ← Always saved
incidents table      ← Only if severity is "high" or "critical"
```

---

## 📊 Test 1 — PSI (Population Stability Index)

**File:** `app/services/drift/metrics.py → calculate_psi()`

PSI is the industry-standard test used in banking and finance to detect whether a population has changed.

### How it works:
1. Divide the **Baseline** data into 10 equal-frequency buckets (percentile bins).
2. Calculate what % of the **Baseline** falls in each bucket (e.g., 10% per bucket).
3. Calculate what % of the **Production** data falls in the same buckets.
4. Measure the divergence between these two distributions.

**Formula:**
```
PSI = Σ (current_% - reference_%) × ln(current_% / reference_%)
```

### Score Interpretation:

| PSI Score | Severity | Meaning |
|---|---|---|
| `< 0.1` | `low` | No significant drift. Model is stable. |
| `0.1 – 0.2` | `medium` | Moderate drift. Monitor closely. |
| `0.2 – 0.3` | `medium` | Warning. Revalidation recommended. |
| `0.3 – 0.5` | `high` | Significant shift. Consider retraining. |
| `> 0.5` | `critical` | Major shift. Model likely invalid. **Incident created.** |

### Implementation Note:
- Zero-values in bins are replaced with `0.0001` to avoid `log(0)` errors.
- Breakpoints are deduplicated to handle constant-value columns.

---

## 📊 Test 2 — KS Test (Kolmogorov-Smirnov)

**File:** `app/services/drift/metrics.py → calculate_ks()`

The KS test is a non-parametric statistical test that measures the maximum distance between two cumulative distribution functions (CDFs).

### How it works:
- Compares the **shape** of the Baseline curve vs the Production curve.
- Returns a `statistic` (distance) and a `p-value` (probability that the shift is random noise).

**Interpretation:**
- **`ks_score`**: Distance between distributions (0.0 = identical, 1.0 = completely different).
- **`ks_pvalue`**: If `< 0.05`, the shift is statistically significant (95% confidence it's real drift, not noise).

### Combined Drift Score:
The final `drift_score` is the **maximum** of PSI and KS scores:
```python
drift_score = max(psi_score, ks_score)
```
This takes the worst-case signal from either test.

---

## 📊 Test 3 — Concept Drift

**File:** `app/services/drift/concept_drift.py`

Concept drift monitors the **AI's output**, not its input. Even if the input data looks fine, the model may start behaving differently.

### How it works:
1. Retrieves the current run's **prediction logs** from the DB.
2. Looks for a `target` / `prediction` column in the **Baseline** CSV.
3. Runs **PSI + KS** on Baseline predictions vs Current predictions.
4. Saves the result as a `concept_drift` finding.

### Example:
If your fraud model used to flag 5% of transactions as fraudulent, but now it flags 40%, that is concept drift — the model's "opinion" has shifted, even if the transactions look normal.

---

## 🚨 Severity Classification

**File:** `app/services/drift/utils.py → classify_drift_severity()`

| Drift Score | Severity |
|---|---|
| `< 0.2` | `low` |
| `0.2 – 0.3` | `medium` |
| `0.3 – 0.5` | `high` |
| `>= 0.5` | `critical` |

---

## 🚨 Incident Escalation

**File:** `app/services/drift/storage.py`

An **Incident** is automatically created if severity is `high` or `critical`.

| Drift Type | Incident Title |
|---|---|
| `data_drift` | `"Data Drift Detected: {feature_name}"` |
| `concept_drift` | `"Concept Drift Detected: Prediction Output"` |

The incident record contains:
- `title`: Human-readable name.
- `description`: PSI and KS scores with severity.
- `failure_type`: `data_drift` or `concept_drift`.
- `finding_id`: Link back to the specific `DriftFinding` row.
- `severity`: `high` or `critical`.
- `status`: Starts as `open`.

---

## 💾 Database Tables

### `drift_findings`
| Column | Type | Description |
|---|---|---|
| `run_id` | FK | Which pipeline run produced this |
| `feature_name` | String | Column name (or `prediction_output`) |
| `psi_score` | Float | PSI result |
| `ks_score` | Float | KS statistic |
| `ks_pvalue` | Float | KS p-value |
| `drift_score` | Float | Max of PSI and KS |
| `drift_detected` | Boolean | True if drift_score > 0.2 |
| `severity` | String | `low` / `medium` / `high` / `critical` |

### `incidents`
| Column | Type | Description |
|---|---|---|
| `run_id` | FK | The pipeline run that triggered this |
| `title` | String | Short description |
| `description` | String | Full details with scores |
| `failure_type` | String | `data_drift` or `concept_drift` |
| `severity` | String | `high` or `critical` |
| `status` | String | `open` (default) |
