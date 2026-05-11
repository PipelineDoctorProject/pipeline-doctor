# API Reference

Base URL: `http://127.0.0.1:8000`
Interactive Docs: `http://127.0.0.1:8000/docs`

All protected endpoints require a `Bearer` JWT token in the `Authorization` header.

---

## 🔐 Auth

### `POST /auth/signup`
Register a new user account. Sends an OTP to the provided email.

**Body:**
```json
{ "email": "user@example.com", "password": "yourpassword" }
```
**Response:** `{ "message": "OTP sent" }`

---

### `POST /auth/verify-otp`
Verify the OTP received by email. Returns JWT tokens.

**Body:**
```json
{ "email": "user@example.com", "otp": "482910" }
```
**Response:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "onboarding_required": true
}
```

---

### `POST /auth/login`
Login with email and password. Returns JWT tokens.

**Body:**
```json
{ "email": "user@example.com", "password": "yourpassword" }
```
**Response:**
```json
{ "access_token": "...", "refresh_token": "..." }
```

---

### `POST /auth/refresh`
Get a new access token using a valid refresh token.

**Body:**
```json
{ "refresh_token": "..." }
```
**Response:**
```json
{ "access_token": "...", "token_type": "bearer" }
```

---

## 🏢 Onboarding & Team Management

### `POST /onboarding/company`
Create a company (Tenant). Assigns the user to an isolated PostgreSQL schema.

**Body:**
```json
{ "company_name": "Acme Corp" }
```
**Response:**
```json
{
  "message": "Company created",
  "tenant_id": "uuid...",
  "schema_name": "tenant_acme_corp_a1b2c3",
  "access_token": "...",
  "refresh_token": "..."
}
```

---

### `POST /invite/send`
*(Admin only)* Send an email invitation to a new team member.

**Body:**
```json
{ "email": "newmember@example.com" }
```

---

### `POST /invite/accept`
Accept a team invitation using the token from the invite email.

**Query param:** `?token=<invite_token>`

---

## 🤖 ML Models

### `POST /ml-models/`
Register a new ML model from MLflow.

**Body:**
```json
{
  "name": "My Production Model",
  "version": "1.0",
  "framework": "sklearn",
  "mlflow_model_name": "PipelineDoctorDemoModel",
  "mlflow_alias": "champion",
  "mlflow_tracking_uri": "http://127.0.0.1:5000",
  "expected_features": ["age", "salary", "bonus"]
}
```

---

### `GET /ml-models/`
List all registered ML models.

---

## 📊 Baselines

### `POST /baseline/upload`
Upload a CSV to create a Baseline profile for a model.

**Query param:** `?model_id=1`
**Body:** `multipart/form-data` with `file` field (CSV).

---

## 🔍 Schema Management

### `GET /schema-change-events`
List all detected schema evolution events (new/missing columns).

---

### `POST /schema/approve/{id}`
Approve a schema change event, allowing the new column structure.

---

## 🏃 Pipeline Runs

### `GET /runs`
List all pipeline run records.

**Response fields:** `id`, `model_id`, `status`, `baseline_version`, `cleaned_data_path`, `created_at`

---

## 📈 Predictions

### `GET /predictions`
List all prediction logs.

**Response fields:** `id`, `run_id`, `input_data`, `prediction`, `created_at`

---

## 🌊 Drift Findings

### `GET /drift-findings`
List all drift analysis results.

**Response fields:** `id`, `run_id`, `feature_name`, `psi_score`, `ks_score`, `ks_pvalue`, `drift_score`, `drift_detected`, `severity`

---

## 🚨 Incidents

### `GET /incidents`
List all auto-generated production incidents.

**Response fields:** `id`, `run_id`, `title`, `description`, `failure_type`, `severity`, `status`, `created_at`

---

## 🔎 Data Quality Findings

### `GET /data-quality-findings`
List all data quality check results.

**Response fields:** `id`, `run_id`, `column_name`, `check_type`, `success`, `details`

---

## ❤️ Health

### `GET /health`
Ping endpoint to verify the server is running.

**Response:** `{ "status": "ok" }`
