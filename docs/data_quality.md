# Data Quality Checks

The Data Quality layer is the first line of defense. It validates each incoming CSV against the active baseline before the batch is trusted for prediction, drift analysis, or RCA.

---

## Overall Flow

```text
Incoming CSV
    |
Save uploaded file
    |
Load active baseline
    |
Schema evolution check
    |
Run validation rules
    |
Transform and align cleaned data
    |
Store DataQualityFindings
    |
Optionally trigger prediction, drift, and RCA
```

---

## Baseline System

A baseline is a stored reference profile created from a known-good dataset.

### What gets stored

| Field | Example | Description |
|---|---|---|
| `schema` | `{"age": "int64"}` | Column name to data type map |
| `profile.min` | `25` | Minimum observed numeric value |
| `profile.max` | `65` | Maximum observed numeric value |
| `profile.null_ratio` | `0.02` | Null percentage in baseline |
| `profile.unique_values` | `["A", "B", "C"]` | Allowed values for categorical columns |

### Baseline versioning

- every upload creates a new version
- the first baseline is auto-approved and active
- later uploads start as draft
- only one baseline can be active per model

---

## Validation Rules

### 1. Schema type validation

**File:** `backend/fastapi/app/services/quality/validator.py`

Compares incoming column types with the baseline schema.

| Scenario | Result |
|---|---|
| baseline type matches incoming type | pass |
| type mismatch | failure stored as `schema_type_mismatch` |

### 2. Null ratio validation

Calculates the percentage of nulls per column.

| Null ratio | Result |
|---|---|
| within threshold | pass |
| above threshold | failure stored as `null_ratio` |

### 3. Numeric range validation

Checks whether numeric values stay within the baseline min and max range.

| Scenario | Result |
|---|---|
| value range stays inside baseline | pass |
| values move outside baseline range | failure stored as `range` |

### 4. Categorical value validation

Checks whether incoming categorical values were already seen in the baseline.

| Scenario | Result |
|---|---|
| all values are known | pass |
| new category appears | failure stored as `categorical` |

---

## Schema Evolution

**File:** `backend/fastapi/app/services/quality/schema_handler.py`

Before validation, the system compares the incoming schema with the active baseline:

- extra columns are flagged as schema change events
- missing columns are added back as `None` to avoid crashes
- the cleaned dataframe is reordered to match the baseline contract

### Approval flow

1. new or missing columns are detected
2. a `schema_change_events` record is stored with `pending` status
3. an admin can review and approve the change
4. a new baseline can later be uploaded to make the change official

---

## Cleaned Output

**File:** `backend/fastapi/app/services/quality/pipeline.py`

After validation and transformation, the pipeline writes a cleaned CSV:

- saved as `cleaned/{run_id}.csv`
- stored on the run as `cleaned_data_path`
- later used by drift detection

When running in Docker, `/app/cleaned` is backed by the Docker volume `backend_cleaned`, so the file may exist in the container volume instead of the local repo folder unless a bind mount is used.

---

## Stored Findings

Failures are stored in `data_quality_findings` with fields such as:

- `pipeline_run_id`
- `column_name`
- `check_type`
- `success`
- `details`
- `created_at`

These stored findings are the source of truth for the Data Quality page.

---

## AI Explanation Layer

The Data Quality page now includes an optional explanation layer for a selected run.

### What it does

It does not decide whether a check failed. The deterministic validators already do that.

Instead, it explains:

- `Why This Matters`
- `Suggested Remediation`

### Endpoint

`GET /data-quality/explain?run_id=<run_id>`

### Behavior

- if a live LLM is configured, the backend generates a short explanation from the stored failed findings
- if no LLM is available, the backend returns a structured deterministic fallback explanation
- the validation table and grouped issue cards remain the source of truth

This keeps the page safe for production use:

- rules detect
- AI explains

---

## Related Files

- `backend/fastapi/app/api/routes/data_quality.py`
- `backend/fastapi/app/services/quality/pipeline.py`
- `backend/fastapi/app/services/quality/validator.py`
- `backend/fastapi/app/services/ai_explanations/insight_explainer.py`
- `frontend/src/pages/data-quality/DataQualityPage.jsx`
