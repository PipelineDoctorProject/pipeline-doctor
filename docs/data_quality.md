# Data Quality and Cleaning Gate

The Data Quality layer is now a production-style acceptance gate, not just a passive checker.

Its job is to answer:

- can this batch be trusted for downstream prediction and drift analysis?
- which rows or values were repaired safely?
- which rows were too corrupted and had to be quarantined?

---

## Current Flow

```text
Incoming CSV
    |
Load active baseline
    |
Detect schema differences
    |
Raw validation against baseline
    |
Cleaning and sanitization
    |
Quarantine heavily corrupted rows
    |
Post-clean validation
    |
Quality gate
    |
    +--> fail: mark run failed, skip prediction and drift, queue RCA
    |
    +--> pass: save cleaned CSV, run prediction, run drift, queue RCA
```

---

## Baseline Profiling

The baseline is created from a known-good dataset and stores two things:

- `schema`
- `profile`

### Schema

Maps each column to a normalized type such as:

- `int`
- `float`
- `bool`
- `object`

### Profile

The profile is column-aware:

#### Numeric columns

Stores:

- `min`
- `max`
- `mean`
- `median`
- `p01`
- `p99`

`p01` and `p99` are used as safer operating bounds than exact raw min/max.

#### Identifier columns

Columns like `id`, `uuid`, or `...id` are treated as identifiers, not strict enums.

#### High-cardinality text columns

Columns with too many unique values are treated as text/high-cardinality fields instead of strict enum categories.

#### Enum-style categorical columns

Only low-cardinality stable categories are validated as explicit allowed values.

---

## Validation Rules

### 1. Schema type validation

Checks whether incoming values are compatible with the expected type.

Examples:

- `float` column receiving numeric-looking strings can still be coerced
- a required numeric column full of invalid text fails

Stored finding type:

- `schema_type_mismatch`

### 2. Null ratio validation

Checks missingness per column.

Default threshold:

- `DATA_QUALITY_NULL_RATIO_THRESHOLD = 0.30`

Stored finding type:

- `null_ratio`

### 3. Numeric range validation

Checks whether current numeric values move outside baseline bounds.

Current validation prefers:

- `p01`
- `p99`

Fallback:

- `min`
- `max`

Stored finding type:

- `range`

### 4. Enum categorical validation

Checks only stable enum-like categories against baseline values.

Identifier columns and high-cardinality text are not treated as strict enums anymore.

Stored finding type:

- `categorical`

---

## Cleaning and Sanitization

The cleaner does more than basic fillna.

### Missing marker normalization

These values are normalized to missing:

- empty string
- `NA`
- `N/A`
- `NULL`
- `NONE`
- `NAN`

### Numeric sanitization

- coercion failures become missing
- out-of-range numeric values are masked
- numeric nulls are filled from:
  - current-batch median
  - baseline median or mean
  - midpoint of baseline bounds
  - `0` as last fallback

### Boolean sanitization

Only explicit boolean tokens are trusted, such as:

- `true`, `false`
- `1`, `0`
- `yes`, `no`

Invalid boolean-like values are treated as issues instead of blindly becoming `True`.

### Categorical sanitization

- invalid enum values are masked
- enum nulls are filled from a valid mode or baseline value
- identifier fields use `UNKNOWN_ID`
- non-enum text fields are normalized but not forced into a small category set

### Row quarantine

Each row accumulates issue counts.

Rows whose issue ratio crosses:

- `DATA_QUALITY_ROW_ISSUE_THRESHOLD = 0.70`

are removed from the accepted dataset and written to quarantine.

---

## Quality Gate

After cleaning, the accepted dataset is validated again.

The run is blocked when any of these are true:

- cleaned row count is `0`
- cleaned row count is below `DATA_QUALITY_MIN_CLEAN_ROW_COUNT`
- cleaned row ratio is below `DATA_QUALITY_MIN_CLEAN_ROW_RATIO`
- required baseline columns are missing
- post-clean schema/type errors remain
- post-clean validation checks still fail

Current defaults:

| Setting | Default |
|---|---|
| `DATA_QUALITY_NULL_RATIO_THRESHOLD` | `0.30` |
| `DATA_QUALITY_ROW_ISSUE_THRESHOLD` | `0.70` |
| `DATA_QUALITY_MIN_CLEAN_ROW_COUNT` | `10` |
| `DATA_QUALITY_MIN_CLEAN_ROW_RATIO` | `0.50` |
| `DATA_QUALITY_CATEGORICAL_LIMIT` | `50` |
| `DATA_QUALITY_HIGH_CARDINALITY_LIMIT` | `200` |
| `DATA_QUALITY_HIGH_CARDINALITY_RATIO` | `0.20` |

---

## Output Artifacts

### Accepted dataset

- path: `cleaned/{run_id}.csv`
- stored on `pipeline_runs.cleaned_data_path`
- used for prediction, drift, and remediation

### Quarantine dataset

- path: `cleaned/quarantine/{run_id}.csv`
- contains removed rows that were too corrupted to trust

When running in Docker, these live in the `backend_cleaned` volume under `/app/cleaned`.

---

## Stored Findings

Raw validation findings are stored in `data_quality_findings`.

That means:

- the UI still shows what originally failed
- RCA still has access to the raw evidence
- the cleaned accepted dataset can still pass the gate even when the raw upload was bad

This distinction is intentional:

- raw findings explain the problem
- post-clean validation decides whether downstream steps are allowed

---

## Downstream Rules

### If quality gate passes

- run status becomes `success`
- predictions may run
- drift detection may run
- doctor RCA is queued

### If quality gate fails

- run status becomes `failed`
- predictions are skipped
- drift detection is skipped
- doctor RCA is still queued so the failure is explainable

---

## Related Files

- `backend/fastapi/app/services/quality/baseline.py`
- `backend/fastapi/app/services/quality/validator.py`
- `backend/fastapi/app/services/quality/transformer.py`
- `backend/fastapi/app/services/quality/pipeline.py`
- `backend/fastapi/app/api/routes/data_quality.py`

---

## Related Docs

- [schema_evolution.md](./schema_evolution.md)
- [drift_detection.md](./drift_detection.md)
- [remediation.md](./remediation.md)
- [automation_and_scheduler.md](./automation_and_scheduler.md)
