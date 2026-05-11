# Database Schema

PipelineDoctor uses **PostgreSQL** (hosted on Supabase). The schema is split into two layers:
- **`public` schema** — Shared tables for auth, tenants, and core pipeline data.
- **Tenant schemas** — Isolated tables per company (e.g., `tenant_acme_a1b2c3`).

Migrations are managed by **Alembic**.

---

## 👤 `users` table

Stores all platform users across all tenants.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Auto-generated |
| `email` | String (Unique) | Login identifier |
| `hashed_password` | String | Bcrypt hash. Null for invited users |
| `tenant_id` | String (FK) | Links to `tenants.id`. Null before onboarding |
| `is_verified` | Boolean | `False` until OTP verified |
| `otp_code` | String | Temporary code, cleared after use |
| `role` | String | `admin` (creator) or `member` (invited) |
| `invite_token` | String | UUID token for team invitations |
| `invite_accepted` | Boolean | Whether the invite link was used |

---

## 🏢 `tenants` table

Represents a company / organization.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Auto-generated |
| `name` | String | Company display name |
| `schema_name` | String (Unique) | e.g., `tenant_acme_a1b2c3` — the PostgreSQL schema |

---

## 🤖 `ml_models` table

Stores MLflow model metadata registered by users.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `name` | String | Friendly model name |
| `version` | String | User-defined version label |
| `framework` | String | e.g., `sklearn`, `xgboost` |
| `mlflow_model_name` | String | Exact name in MLflow registry |
| `mlflow_alias` | String | e.g., `champion`. Default used if null |
| `mlflow_run_id` | String | Optional: specific MLflow run ID |
| `mlflow_tracking_uri` | String | Remote MLflow server URL |
| `expected_features` | JSON | Ordered list of feature column names |
| `created_at` | Timestamp | Record creation time |

---

## 📊 `baselines` table

Stores statistical profiles of training/reference data.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `model_id` | Integer (FK) | Links to `ml_models.id` |
| `version` | Integer | Increments per upload (v1, v2...) |
| `schema` | JSON | `{ "column_name": "dtype" }` map |
| `profile` | JSON | `{ "column": { "min", "max", "unique_values" } }` |
| `status` | String | `draft` → `approved` |
| `is_active` | Boolean | Only one active baseline per model |
| `file_path` | String | Path to the uploaded CSV file |

---

## 🏃 `pipeline_runs` table

A record for every execution of `run_auto_runner.py`.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `model_id` | Integer (FK) | Which model was used |
| `baseline_version` | Integer | Baseline version used |
| `status` | String | `running` / `completed` / `failed` |
| `cleaned_data_path` | String | Path to the output cleaned CSV |
| `created_at` | Timestamp | When the run started |

---

## 🔄 `schema_change_events` table

Tracks detected changes in incoming CSV structure vs the active baseline.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `model_id` | Integer (FK) | Which model's pipeline detected this |
| `pipeline_run_id` | Integer (FK) | The specific run that triggered it |
| `baseline_id` | Integer (FK) | Which baseline was active |
| `new_columns` | JSON | List of added columns (e.g., `["name"]`) |
| `missing_columns` | JSON | List of removed columns |
| `status` | String | `pending` → `approved` / `rejected` |

---

## 🔍 `data_quality_findings` table

One row per check per column per pipeline run.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `run_id` | Integer (FK) | Links to `pipeline_runs.id` |
| `column_name` | String | Which column was checked |
| `check_type` | String | `null_ratio` / `range` / `categorical` |
| `success` | Boolean | `True` = passed, `False` = failed |
| `details` | String | Human-readable description |

---

## 🌊 `drift_findings` table

One row per feature per pipeline run.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `run_id` | Integer (FK) | Links to `pipeline_runs.id` |
| `feature_name` | String | Column name (or `prediction_output`) |
| `psi_score` | Float | Population Stability Index score |
| `ks_score` | Float | KS test statistic |
| `ks_pvalue` | Float | KS p-value |
| `drift_score` | Float | `max(psi_score, ks_score)` |
| `drift_detected` | Boolean | `True` if `drift_score > 0.2` |
| `severity` | String | `low` / `medium` / `high` / `critical` |
| `created_at` | Timestamp | When the finding was saved |

---

## 🚨 `incidents` table

Auto-created when drift severity is `high` or `critical`.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `run_id` | Integer (FK) | Links to `pipeline_runs.id` |
| `title` | String | Short description |
| `description` | String | Full details with PSI/KS scores |
| `failure_type` | String | `data_drift` or `concept_drift` |
| `finding_type` | String | `drift` |
| `finding_id` | Integer | FK to `drift_findings.id` |
| `severity` | String | `high` or `critical` |
| `status` | String | `open` (default) |
| `created_at` | Timestamp | When the incident was opened |

---

## 🔮 `prediction_logs` table

One row per row of data per pipeline run.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `run_id` | Integer (FK) | Links to `pipeline_runs.id` |
| `input_data` | JSON | `{ "features": [val1, val2, ...] }` |
| `prediction` | JSON | `{ "value": 1 }` |
| `created_at` | Timestamp | Inference timestamp |

---

## 🗺️ Entity Relationship Overview

```
users ──────────── tenants
  │
ml_models ─────── baselines
  │
pipeline_runs ──┬─ data_quality_findings
                ├─ schema_change_events
                ├─ drift_findings ──── incidents
                └─ prediction_logs
```
