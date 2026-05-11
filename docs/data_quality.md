# Data Quality Checks

The Data Quality layer is the first line of defense. It processes every incoming CSV file and validates it against the stored **Baseline** before allowing it to reach the ML model.

---

## 🔄 Overall Flow

```
Incoming CSV
    ↓
Load Active Baseline  ←─ (DB: baselines table)
    ↓
Schema Evolution Check  ←─ detects new/missing columns
    ↓
DataValidator runs 4 checks:
   1. Type Validation
   2. Null Ratio Check
   3. Numeric Range Check
   4. Categorical Value Check
    ↓
Store DataQualityFindings  ←─ (DB: data_quality_findings)
    ↓
Pass cleaned CSV to Prediction Layer
```

---

## 📊 Baseline System

A **Baseline** is a statistical profile extracted from your training/reference CSV. It acts as the "source of truth" for all future validation.

### What gets stored per column?
| Field | Example | Description |
|---|---|---|
| `schema` | `{"age": "int64"}` | Column name → data type map |
| `profile.min` | `25` | Minimum observed value |
| `profile.max` | `65` | Maximum observed value |
| `profile.null_ratio` | `0.02` | % of nulls in training data |
| `profile.unique_values` | `["A", "B", "C"]` | For categorical columns |

### Baseline Versioning
- Every new upload creates a new **version** (v1, v2, v3...).
- The **first** upload is auto-approved and set as `active`.
- Subsequent uploads start as `draft` and require manual approval.
- Only **one** baseline can be `active` at a time per model.

### API
```
POST /baseline/upload?model_id=1   ← Upload a CSV as baseline
```

---

## 🧪 Check 1 — Schema Type Validation

**File:** `app/services/quality/validator.py → validate_schema()`

Compares the data type of each column in the incoming CSV against the baseline schema.

| Scenario | Example | Result |
|---|---|---|
| Types match | Baseline: `int64`, CSV: `int64` | ✅ PASS |
| Type mismatch | Baseline: `int64`, CSV: `object` | ❌ Schema Error logged |

> Schema errors do **not** stop the pipeline. They are logged and the file continues processing.

---

## 🧪 Check 2 — Null Ratio Validation

**File:** `app/services/quality/validator.py → validate_nulls()`

Calculates the percentage of `NaN` / `null` values per column.

**Default Threshold:** `30%` (0.3)

| Null % | Result |
|---|---|
| 0% – 30% | ✅ PASS |
| > 30% | ❌ FAIL — Finding saved |

**Example output:**
```json
{ "column": "age", "check": "null_ratio", "success": true, "details": "0.00 (threshold=0.3)" }
```

---

## 🧪 Check 3 — Numeric Range Validation

**File:** `app/services/quality/validator.py → validate_numeric_ranges()`

Checks that all numeric values in the CSV fall within the min-max range observed in the Baseline.

| Scenario | Result |
|---|---|
| CSV range within baseline | ✅ PASS |
| CSV has values outside baseline range | ❌ FAIL |

**Example output:**
```json
{ "column": "age", "check": "range", "success": false, "details": "29.0-55.0 vs 25.0-51.0" }
```
> Here, the production data has an age range of 29–55, but the baseline was 25–51. The maximum is out of range — `FAIL`.

---

## 🧪 Check 4 — Categorical Value Validation

**File:** `app/services/quality/validator.py → validate_categorical()`

For columns with a known set of allowed values (e.g., `["A", "B", "C"]`), this check flags any "unseen" categories.

| Scenario | Result |
|---|---|
| All values are in the allowed set | ✅ PASS |
| New value not in training data appears | ❌ FAIL — `unseen=['D']` |

---

## 🔍 Schema Evolution Detection

**File:** `app/services/quality/schema_handler.py`

Before running the checks, the pipeline performs a schema diff:

- **Extra columns**: Columns in the CSV that are **not** in the baseline. These are flagged as `schema_change_events` with status `pending`.
- **Missing columns**: Columns in the baseline that are **missing** from the CSV. Filled with `None` to avoid crashes.

The pipeline then drops extra columns and reorders the CSV to match the baseline exactly before further processing.

### Schema Approval Workflow
1. A new column arrives → `schema_change_events` record created (status: `pending`).
2. Admin reviews and **approves** via `POST /schema/approve/{id}`.
3. Data Scientist retrains model → uploads new baseline including the new column.
4. System now monitors the new column for drift.

---

## 💾 Storage

All check results are saved to the **`data_quality_findings`** table with:
- `run_id`: Which pipeline run triggered this.
- `column_name`: Which column was checked.
- `check_type`: `null_ratio`, `range`, or `categorical`.
- `success`: `true` / `false`.
- `details`: Human-readable explanation.
