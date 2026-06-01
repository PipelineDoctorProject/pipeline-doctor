# Authentication and Tenant Isolation

PipelineDoctor uses JWT auth, OTP verification, invite-based member onboarding, and schema-based multi-tenancy.

---

## Account and Workspace Flow

### 1. Self-register

- Endpoint: `POST /auth/signup`
- Input: `email`, `password`
- Behavior:
  - normalizes email
  - hashes the password
  - creates the user
  - sends a 6-digit OTP
- Workspace role:
  - self-registered users become `admin`

### 2. Verify OTP

- Endpoint: `POST /auth/verify-otp`
- Output:
  - `access_token`
  - `refresh_token`
  - `token_type`
  - `onboarding_required`
- Behavior:
  - marks the user verified
  - clears OTP state
  - issues the first JWT pair
  - sends the user into onboarding when they do not yet belong to a tenant

### 3. Workspace onboarding

- Endpoint: `POST /onboarding/company`
- Input: `company_name`
- Output:
  - `tenant_id`
  - `workspace_name`
  - `schema_name`
  - refreshed `access_token` and `refresh_token`
- Frontend flow:
  - step 1: create workspace
  - step 2: invite members or skip
  - only after step 2 does the user move to the dashboard

### 4. Invite members

- Endpoint: `POST /invite/member`
- Admin only
- Behavior:
  - creates a pre-linked member account inside the admin's tenant
  - assigns `role = "member"`
  - emails an invite token

### 5. Accept invite

- Endpoint: `POST /invite/accept`
- Input: `token`, `password`
- Output:
  - `access_token`
  - `refresh_token`
  - `token_type`
- Behavior:
  - sets the member password
  - marks the invite accepted
  - marks the member verified
  - signs the member into the workspace immediately

### 6. Login and refresh

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

The backend returns bearer tokens in the JSON response and also sets auth cookies for browser flows.

---

## Token Strategy

| Token | Default lifetime | Purpose |
|---|---|---|
| Access token | 30 minutes | main authenticated API access |
| Refresh token | 7 days | access-token renewal |

JWT payload includes:

- `user_id`
- `tenant_id`
- `schema_name`
- `role`
- `type`

---

## Cookie and Header Behavior

Auth uses environment-aware cookie settings:

- local HTTP:
  - `secure = false`
  - `samesite = lax`
- HTTPS:
  - `secure = true`
  - `samesite = none`

Important runtime rule:

- the backend prefers the `Authorization: Bearer ...` header over stale browser cookies

That prevents cross-session issues where one user could accidentally keep using another user's old cookie state in the same browser.

---

## Tenant Isolation Model

PipelineDoctor uses PostgreSQL schema-based isolation.

### Public schema

Shared tables live in `public`, including:

- `users`
- `tenants`
- Slack workspace connection metadata

### Tenant schemas

Each workspace gets a dedicated schema such as:

`tenant_acme_a1b2c3`

Tenant-scoped tables include:

- `ml_models`
- `baselines`
- `pipeline_runs`
- `data_quality_findings`
- `drift_findings`
- `incident_groups`
- `incidents`
- `agent_runs`
- `agent_step_logs`
- `remediation_runs`
- `remediation_action_logs`

### Request routing

For authenticated requests, middleware:

1. decodes the JWT
2. loads the user
3. sets:

```sql
SET search_path TO "<tenant_schema>", public
```

This lets tenant-scoped SQLAlchemy models resolve into the correct tenant schema automatically while still allowing shared `public` references.

---

## Tenant Safety Hardening

The current production-style safeguards are:

- tenant schema bootstrap creates required tenant tables explicitly
- startup repair can backfill missing tenant tables for older partially created workspaces
- model-filtered endpoints verify that the requested `model_id` belongs to the current tenant
- frontend model-selection state is scoped per tenant and per user
- backend remains the final enforcement layer for data ownership

---

## Operational Notes

- invited members should only see their tenant's data
- admins can invite members during onboarding and later from the dashboard
- onboarding returns refreshed tenant-aware tokens; the frontend must store the new access token before calling protected routes

---

## Security Follow-Up

Before production deployment:

- rotate `SECRET_KEY` to a 32+ byte secret
- keep SMTP, Slack, and DB credentials in secure environment management
- add end-to-end auth regression tests for signup, onboarding, invite acceptance, and member login

---

## Related Files

- `backend/fastapi/app/api/routes/auth.py`
- `backend/fastapi/app/api/routes/onboarding.py`
- `backend/fastapi/app/api/routes/invite.py`
- `backend/fastapi/app/middleware/auth_middleware.py`
- `backend/fastapi/app/services/auth/auth_service.py`
- `backend/fastapi/app/services/auth/onboarding_service.py`
- `backend/fastapi/app/services/auth/invite_service.py`
- `backend/fastapi/app/services/auth/accept_invite_service.py`
- `backend/fastapi/app/utils/schema_utils.py`
