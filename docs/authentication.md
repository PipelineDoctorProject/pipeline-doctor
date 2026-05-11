# Authentication & Security

PipelineDoctor uses a multi-stage authentication system designed for security and scalability, featuring JWT-based tokens and OTP (One-Time Password) verification.

## 🔑 Authentication Flow

### 1. User Signup
- **Endpoint**: `POST /auth/signup`
- **Process**:
    - User provides `email` and `password`.
    - System checks for duplicate emails.
    - An OTP is generated and sent to the user's email.
    - User record is created with `is_verified=False`.

### 2. OTP Verification
- **Endpoint**: `POST /auth/verify-otp`
- **Process**:
    - User submits the OTP received via email.
    - If correct, `is_verified` is set to `True`.
    - System issues a pair of tokens: **Access Token** (Short-lived) and **Refresh Token** (Long-lived).
    - Returns `onboarding_required: True` to trigger the user setup flow.

### 3. User Login
- **Endpoint**: `POST /auth/login`
- **Process**:
    - Standard email/password validation using Bcrypt hashing.
    - Issues new Access and Refresh tokens upon success.

---

## 🛡️ Security Implementation

### JWT Token Strategy
- **Algorithm**: HS256 (HMAC with SHA-256).
- **Access Token**: Expires in **30 minutes**. Contains the `user_id`.
- **Refresh Token**: Expires in **7 days**. Used to obtain new access tokens without re-authenticating.
- **Payload Security**: Tokens include a `type` field (`access` or `refresh`) to prevent token-type confusion attacks.

### Password Safety
- Passwords are never stored in plain text.
- Uses **Passlib with Bcrypt** for secure salt-and-hashing.

---

## 🏢 Multi-Tenancy Architecture

PipelineDoctor implements a **Schema-based Multi-Tenancy** strategy, ensuring that data for different organizations is physically isolated at the database level.

### 1. Tenant Isolation
- **Isolated Schemas**: Every "Company" (Tenant) is assigned a unique PostgreSQL schema (e.g., `tenant_google_a1b2c3`).
- **Data Sovereignty**: Tables like `ml_models`, `baselines`, and `incidents` are created inside the tenant's specific schema, not in the public schema.

### 2. Tenant Onboarding
After a user verifies their account via OTP, they must go through the **Onboarding Flow**:
- **Endpoint**: `POST /onboarding/company`
- **Process**:
    - User provides a `company_name`.
    - System generates a unique `schema_name`.
    - System executes `CREATE SCHEMA` and initializes all required tables within that schema.
    - The `user` record is linked to the new `tenant_id`.

### 3. Identity Injection (JWT)
Once a user is associated with a tenant, all future tokens include multi-tenant metadata:
- **`tenant_id`**: The unique UUID of the organization.
- **`schema_name`**: The database schema identifier.
- **`role`**: The user's permissions within that specific tenant.

### 4. Automated Context Switching (Middleware)
A dedicated **Auth Middleware** (`app/middleware/auth_middleware.py`) handles every request:
- It extracts the `tenant_id` from the JWT.
- It automatically executes `SET search_path TO "..."` on the database session.
- This ensures that all SQL queries in the service layer are automatically routed to the correct tenant's tables without the developer having to manually filter by `tenant_id`.

---

## 🚦 Token Refresh Flow
When an access token expires, the client should call:
- **Endpoint**: `POST /auth/refresh`
- **Payload**: `{ "refresh_token": "..." }`
- **Response**: A new valid `access_token`.

---

## 📦 Service Components

- **JWT Core (`app/core/jwt.py`)**: Handles encoding, decoding, and expiration logic.
- **Security Utils (`app/core/security.py`)**: Handles password hashing and verification.
- **Auth Service (`app/services/auth/auth_service.py`)**: Business logic for signup, login, and OTP management.
- **Email Utils (`app/utils/email_utils.py`)**: Orchestrates sending OTPs to users.
