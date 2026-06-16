# CI/CD And IaC Setup

OpsSight uses GitHub Actions for CI/CD, Terraform for Azure infrastructure, and Ansible for post-provision operational checks.

The production idea is simple:

```text
Pull request
  -> CI validates code, Docker builds, Terraform, and Ansible syntax
Merge/release
  -> Images are built and pushed to Azure Container Registry
IaC workflow
  -> Terraform provisions/updates Azure infrastructure and Container Apps
Migration job
  -> Alembic and tenant repair run once
Deploy
  -> API and frontend Container Apps run the selected immutable image tag
Verify
  -> Ansible checks environment readiness
```

## Workflows

| Workflow | File | Purpose |
|---|---|---|
| CI | `.github/workflows/ci.yml` | Validates backend, frontend, Docker, Terraform, and Ansible on PRs and pushes. |
| Container Release | `.github/workflows/container-release.yml` | Manually builds backend/frontend images, verifies frontend build config, and optionally pushes images to Azure Container Registry. |
| IaC | `.github/workflows/iac.yml` | Manually runs Terraform `plan` or `apply` for `dev`, `staging`, or `prod`, including Azure Container Apps. |
| Ansible Operations | `.github/workflows/ansible.yml` | Manually runs post-provision verification playbooks. |

## CI Checks

The CI workflow currently runs:

- Python dependency install, compile check, and backend tests.
- Frontend dependency install, ESLint, and Vite production build.
- Docker Compose validation for local and production example files.
- Backend Docker image build.
- Frontend Docker image build.
- Terraform format and validation for dev/prod.
- Ansible syntax check.

## Production Compose Reference

`docker-compose.prod.example.yml` is a production topology reference for environments that still run Docker Compose directly. It expects pushed image names and keeps runtime secrets outside git.

Required image variables:

- `OPSSIGHT_BACKEND_IMAGE`
- `OPSSIGHT_FRONTEND_IMAGE`

Optional env file override:

- `OPSSIGHT_BACKEND_ENV_FILE`

If `OPSSIGHT_BACKEND_ENV_FILE` is not set, Compose falls back to `backend/fastapi/.env.example` so CI can validate the file without needing real secrets. In production, set it to a secret-backed file such as `backend/fastapi/.env.production`, or preferably inject secrets through the platform runtime such as Azure Container Apps secrets.

## GitHub Environments

Create these GitHub Environments:

- `dev`
- `staging`
- `prod`

Recommended protection:

- `dev`: no approval or one lightweight reviewer.
- `staging`: at least one reviewer.
- `prod`: required reviewer approval, no self-approval if possible.

## Required GitHub Environment Values

For Azure OIDC, store these as GitHub Environment secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

For Azure Container Registry, store these as GitHub Environment variables or secrets:

- `AZURE_CONTAINER_REGISTRY_NAME`
- `AZURE_CONTAINER_REGISTRY_LOGIN_SERVER`

For frontend builds, store these as GitHub Environment variables or secrets:

- `VITE_API_URL`
- `VITE_WS_URL`

For API runtime, store at least these as GitHub Environment secrets:

- `API_SECRET_KEY`
- `API_DB_NAME`
- `API_DB_USER`
- `API_DB_PASSWORD`
- `API_DB_HOST`

Optional API runtime values include:

- `API_DB_PORT`
- `API_DB_SSLMODE`
- `API_ALGORITHM`
- `API_REDIS_URL`
- `API_MLFLOW_TRACKING_URI`
- `API_GROQ_API_KEY`
- `API_MAIL_USERNAME`
- `API_MAIL_PASSWORD`
- `API_MAIL_FROM`
- `API_SLACK_CLIENT_ID`
- `API_SLACK_CLIENT_SECRET`

For MLflow infrastructure, store this as a GitHub Environment secret:

- `MLFLOW_POSTGRESQL_ADMIN_PASSWORD`

Leave `MLFLOW_BACKEND_STORE_URI` and `MLFLOW_ARTIFACT_ROOT` unset unless you intentionally want to override the Terraform-managed Azure PostgreSQL Flexible Server and Azure Blob artifact container.

Do not store database passwords, Slack tokens, JWT secrets, or API keys in the repository. Use GitHub Environment secrets, Azure Key Vault, or Container App secrets.

## Terraform

Terraform lives in `deploy/terraform`.

Current structure:

- `deploy/terraform/modules/container_apps`: reusable Azure platform module.
- `deploy/terraform/environments/dev`: development infrastructure.
- `deploy/terraform/environments/prod`: production infrastructure.

Current Terraform resources:

- Azure Resource Group
- Azure Container Registry
- Log Analytics Workspace
- Azure Container Apps Environment
- FastAPI API Container App
- Frontend Container App
- Celery worker Container App
- Celery beat Container App
- MLflow Container App
- Azure Cache for Redis
- Azure PostgreSQL Flexible Server for MLflow metadata
- Azure Blob Storage for MLflow artifacts
- Azure Blob Storage for app uploads, cleaned data, reports, and exports

The API and frontend image tag is controlled by the IaC workflow `image_tag` input. Use immutable tags such as `dev-005`, `staging-014`, or a release SHA. Avoid relying on `dev-latest` for real deploys because it makes rollbacks and verification ambiguous.

The IaC workflow writes a generated `zz-workflow.auto.tfvars.json` file so the workflow `image_tag` input wins over checked-in defaults.

Run locally:

```bash
terraform -chdir=deploy/terraform/environments/dev init
terraform -chdir=deploy/terraform/environments/dev plan
terraform -chdir=deploy/terraform/environments/dev apply
```

For production, prefer the protected GitHub `IaC` workflow instead of local apply.

## Ansible

Ansible lives in `deploy/ansible`.

Current structure:

- `inventories/dev`
- `inventories/prod`
- `playbooks/site.yml`
- `playbooks/verify.yml`
- `roles/opssight_runtime`

Current Ansible role validates runtime configuration expectations. It is intentionally safe and non-destructive.

Run locally:

```bash
ansible-playbook deploy/ansible/playbooks/verify.yml -i deploy/ansible/inventories/dev/hosts.ini
```

## Step By Step Setup

1. Push the repository to GitHub.
2. Create `dev`, `staging`, and `prod` GitHub Environments.
3. Configure Azure OIDC federated credentials for this repository.
4. Add the Azure, ACR, frontend, API runtime, and MLflow password values listed above to GitHub Environments.
5. Open a pull request and confirm the `CI` workflow passes.
6. Run `IaC` with `environment=dev` and `action=plan`.
7. Review the Terraform plan.
8. Run `IaC` with `environment=dev` and `action=apply`.
9. Copy the Terraform outputs `container_registry_name`, `container_registry_login_server`, `api_container_app_url`, and `frontend_container_app_url` into the matching GitHub Environment values.
10. Set `VITE_API_URL` to the API URL and `VITE_WS_URL` to the same host with `wss://`.
11. Run `Container Release` with a new immutable `image_tag` and `push_images=true`.
12. Run `IaC` again with `action=apply` and the same `image_tag`.
13. In Azure Container Apps, confirm the active API and frontend revisions use that image tag.
14. Confirm worker and beat Container Apps use the same backend image tag.
15. Confirm MLflow is using the Terraform-managed PostgreSQL server and Blob artifact container.
16. Test `/health` on the API URL and the login flow from the frontend URL.
17. Run `Ansible Operations` with `playbook=verify` when the environment is reachable.

## Branch Strategy

Recommended:

- `feature/*`: implementation work.
- `develop`: integration branch.
- `main`: production-ready branch.

Protect `main` with:

- Required pull request review.
- Required passing CI.
- No direct pushes.
- Required GitHub Environment approval before production deploys.

## Current Boundary

Terraform currently owns the Azure foundation, ACR, API Container App, frontend Container App, worker, beat, MLflow Container App, Azure Cache for Redis, Azure PostgreSQL Flexible Server for MLflow metadata, Azure Blob Storage for MLflow artifacts, and Azure Blob Storage for app uploads/cleaned/report/export artifacts. The application database remains Supabase through `API_DB_*` secrets. One-shot migration jobs, Key Vault references, custom domains, managed Airflow, and production observability still need to be added before a full production rollout.
