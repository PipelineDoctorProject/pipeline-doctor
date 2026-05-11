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

## 📦 Service Components

- **JWT Core (`app/core/jwt.py`)**: Handles encoding, decoding, and expiration logic.
- **Security Utils (`app/core/security.py`)**: Handles password hashing and verification.
- **Auth Service (`app/services/auth/auth_service.py`)**: Business logic for signup, login, and OTP management.
- **Email Utils (`app/utils/email_utils.py`)**: Orchestrates sending OTPs to users.

---

## 🚦 Token Refresh Flow
When an access token expires, the client should call:
- **Endpoint**: `POST /auth/refresh`
- **Payload**: `{ "refresh_token": "..." }`
- **Response**: A new valid `access_token`.
