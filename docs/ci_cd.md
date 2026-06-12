# CI/CD And IaC Setup

OpsSight uses GitHub Actions for CI/CD, Terraform for Azure infrastructure, and Ansible for post-provision operational checks.

The production idea is simple:

```text
Pull request
  -> CI validates code, Docker builds, Terraform, and Ansible syntax
Merge/release
  -> Images are built and pushed to Azure Container Registry
IaC workflow
  -> Terraform provisions Azure infrastructure
Migration job
  -> Alembic and tenant repair run once
Deploy
  -> API, worker, beat, and frontend are updated
Verify
  -> Ansible checks environment readiness
```

## Workflows

| Workflow | File | Purpose |
|---|---|---|
| CI | `.github/workflows/ci.yml` | Validates backend, frontend, Docker, Terraform, and Ansible on PRs and pushes. |
| Container Release | `.github/workflows/container-release.yml` | Manually builds and optionally pushes backend/frontend images to Azure Container Registry. |
| IaC | `.github/workflows/iac.yml` | Manually runs Terraform `plan` or `apply` for `dev` or `prod`. |
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

## Required GitHub Secrets

For Azure OIDC:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

For Azure Container Registry:

- `AZURE_CONTAINER_REGISTRY_NAME`
- `AZURE_CONTAINER_REGISTRY_LOGIN_SERVER`

Later deployment workflows will also need:

- `AZURE_RESOURCE_GROUP`
- `AZURE_CONTAINER_APP_API`
- `AZURE_CONTAINER_APP_WORKER`
- `AZURE_CONTAINER_APP_BEAT`
- `AZURE_CONTAINER_APP_FRONTEND`

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
4. Add the Azure secrets listed above to GitHub Environments.
5. Open a pull request and confirm the `CI` workflow passes.
6. Run `IaC` with `environment=dev` and `action=plan`.
7. Review the Terraform plan.
8. Run `IaC` with `environment=dev` and `action=apply`.
9. Run `Container Release` with `push_images=false`.
10. If builds pass, run `Container Release` with `push_images=true`.
11. Add the final Container Apps deployment update step after Azure app names are finalized.
12. Run `Ansible Operations` with `playbook=verify`.

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

This setup gives us a strong CI/CD and IaC foundation. The next production step is to add the actual Azure Container App resources and deployment update commands after finalizing the Azure topology, domains, and secret strategy.
