# Authentication & Security

PipelineDoctor uses a multi-stage, multi-tenant authentication system designed for security and scalability, featuring JWT-based tokens and OTP (One-Time Password) email verification.

---

## 🔑 Authentication Flow

### 1. User Signup
- **Endpoint**: `POST /auth/signup`
- **Process**:
    - User provides `email` and `password`.
    - System checks for duplicate emails.
    - Password is hashed using **Bcrypt** and stored.
    - A 6-digit OTP is generated and emailed to the user.
    - User record is created with `is_verified=False`.

**Request:**
```json
{ "email": "user@example.com", "password": "yourpassword" }
```
**Response:**
```json
{ "message": "OTP sent" }
```

---

### 2. OTP Verification
- **Endpoint**: `POST /auth/verify-otp`
- **Process**:
    - User submits the OTP received via email.
    - If correct, `is_verified` is set to `True` and `otp_code` is cleared.
    - System issues an **Access Token** (30 min) and a **Refresh Token** (7 days).
    - Returns `onboarding_required: True` to trigger the company setup flow.

**Request:**
```json
{ "email": "user@example.com", "otp": "482910" }
```
**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "onboarding_required": true
}
```

---

### 3. User Login
- **Endpoint**: `POST /auth/login`
- **Process**:
    - Standard email/password validation using Bcrypt verification.
    - Issues new Access and Refresh tokens upon success.

**Request:**
```json
{ "email": "user@example.com", "password": "yourpassword" }
```
**Response:**
```json
{ "access_token": "eyJ...", "refresh_token": "eyJ..." }
```

---

### 4. Token Refresh
- **Endpoint**: `POST /auth/refresh`
- **Process**:
    - Validates the refresh token's signature and `type` field.
    - Issues a fresh access token without requiring re-login.

**Request:**
```json
{ "refresh_token": "eyJ..." }
```
**Response:**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

---

## 🛡️ Security Implementation

### JWT Token Strategy
**File:** `app/core/jwt.py`

| Token Type | Expiry | Contains |
|---|---|---|
| Access Token | 30 minutes | `user_id`, `tenant_id`, `role`, `schema_name` |
| Refresh Token | 7 days | `user_id`, `tenant_id`, `role`, `schema_name` |

- **Algorithm**: HS256 (HMAC with SHA-256).
- **Type Field**: Both tokens contain a `type` field (`"access"` / `"refresh"`) to prevent token-type confusion attacks.
- **Expiry**: Enforced automatically; expired tokens raise a `401 Token expired` error.

### Password Safety
**File:** `app/core/security.py`
- Passwords are **never stored in plain text**.
- Uses **Passlib with Bcrypt** for secure hashing with automatic salting.

---

## 🏢 Multi-Tenancy Architecture

PipelineDoctor implements **PostgreSQL Schema-based Multi-Tenancy**, providing complete physical data isolation between organizations.

### How it works:

```
User Signs Up → Verifies OTP → Creates Company (Onboarding)
                                        ↓
                        PostgreSQL Schema created:
                        "tenant_acmecorp_a1b2c3"
                                        ↓
                        All model/pipeline/drift tables
                        created inside that schema
                                        ↓
                        JWT updated with tenant_id + schema_name
```

### 1. Tenant Isolation
- Every "Company" gets a **dedicated PostgreSQL schema** (e.g., `tenant_acme_a1b2c3`).
- Tables like `ml_models`, `baselines`, `pipeline_runs`, `drift_findings`, and `incidents` exist independently per tenant.
- **No cross-tenant data leakage is possible** at the database level.

### 2. Tenant Onboarding
- **Endpoint**: `POST /onboarding/company`
- **File**: `app/services/auth/onboarding_service.py`

**Process:**
1. User provides a `company_name`.
2. System generates a unique `schema_name` (e.g., `tenant_acme_corp_a1b2c3`).
3. Executes `CREATE SCHEMA IF NOT EXISTS "schema_name"` in PostgreSQL.
4. Dynamically creates all required tables inside the new schema.
5. Links the `user` record to the new `tenant_id`.
6. Issues new tokens now containing `tenant_id`, `schema_name`, and `role`.

**Request:**
```json
{ "company_name": "Acme Corp" }
```
**Response:**
```json
{
  "message": "Company created",
  "tenant_id": "uuid...",
  "schema_name": "tenant_acme_corp_a1b2c3",
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

### 3. Automated Context Switching (Middleware)
**File:** `app/middleware/auth_middleware.py`

Every incoming HTTP request is intercepted by the **AuthMiddleware**:

1. Extracts the `Authorization: Bearer <token>` header.
2. Decodes the JWT and loads the `user` object from the database.
3. If the user has a `tenant_id`, executes:
   ```sql
   SET search_path TO "tenant_acme_corp_a1b2c3", public
   ```
4. All subsequent SQL queries in that request are automatically routed to the correct tenant's tables — **zero manual filtering needed**.

---

## 👥 Team Invite System

**File:** `app/services/auth/invite_service.py`

Admins can invite team members to their tenant workspace.

- **Endpoint**: `POST /invite/send`
- **Who can invite**: Only users with `role = "admin"`.

**Process:**
1. Admin provides the new member's email.
2. System creates a `User` record pre-linked to the admin's `tenant_id` with `role = "member"`.
3. A unique `invite_token` (UUID) is generated and emailed.
4. Member clicks the link → `POST /invite/accept?token=<uuid>` → sets a password and activates account.

---

## 📦 Service & File Map

| File | Responsibility |
|---|---|
| `app/core/jwt.py` | Token creation, decoding, and expiry validation |
| `app/core/security.py` | Bcrypt password hashing and verification |
| `app/services/auth/auth_service.py` | Signup, OTP verify, login, token refresh logic |
| `app/services/auth/onboarding_service.py` | Company creation and schema provisioning |
| `app/services/auth/invite_service.py` | Team member invitation flow |
| `app/services/auth/accept_invite_service.py` | Invite acceptance and account activation |
| `app/middleware/auth_middleware.py` | JWT extraction and DB schema context switching |
| `app/utils/email_utils.py` | SMTP email sending (OTP + invite links) |
| `app/utils/otp_utils.py` | Random 6-digit OTP generation |
| `app/utils/schema_utils.py` | `CREATE SCHEMA` and `SET search_path` utilities |
