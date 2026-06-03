# Auth and Tenant Hardening

This workstream covers onboarding, invite flows, and tenant-isolation reliability.

---

## Delivered

### Onboarding flow

- self-registered users become workspace admins
- OTP verification leads into onboarding
- onboarding step 1 creates the workspace and refreshed tenant-aware tokens
- onboarding step 2 supports member invites before entering the dashboard

### Invite and member flow

- invited members receive an email invite
- invite acceptance sets the password and activates the account
- accepted members can sign in normally afterward

### Tenant-isolation hardening

- API now prefers the current bearer token over stale cookies
- tenant schema creation checks the tenant schema explicitly
- startup repair covers older half-created tenant schemas
- model-scoped endpoints validate that the requested model belongs to the current tenant

---

## Product Result

- new workspaces start with their own tenant schema and tenant tables
- invited members only see their workspace data
- onboarding and member login no longer bounce users back to the wrong page when tokens refresh

---

## Production Value

This closes two critical classes of issues:

- broken onboarding/member-auth transitions
- cross-tenant leakage caused by stale auth state or incomplete tenant provisioning

---

## Related Docs

- [authentication.md](./authentication.md)
- [database_schema.md](./database_schema.md)
- [setup.md](./setup.md)
