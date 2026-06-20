# Terraform Infrastructure

Terraform is the source of truth for Azure infrastructure. It creates and owns the resource group, Azure Container Registry, Log Analytics, the Container Apps environment, and the API/frontend Container Apps.

Application runtime settings are passed from GitHub Environments into Terraform during the `IaC` workflow. Keep secrets in GitHub Environments, Azure Key Vault, or the target platform secret store. Do not commit real secrets in Terraform variables.

## Layout

- `environments/dev`: Development Azure infrastructure.
- `environments/staging`: Staging Azure infrastructure used for production-like validation.
- `environments/prod`: Production Azure infrastructure.
- `modules/container_apps`: Reusable Azure Container Apps platform module.

## GitHub Environments

The repository is set up to use three GitHub Environments:

- `dev`
- `staging`
- `prod`

Each environment should contain the Azure OIDC secrets used by `azure/login`:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

After Terraform creates the Azure Container Registry, add these environment variables to the same GitHub Environment:

- `AZURE_CONTAINER_REGISTRY_NAME`
- `AZURE_CONTAINER_REGISTRY_LOGIN_SERVER`

Frontend build values:

- `VITE_API_URL`
- `VITE_WS_URL`

Required API runtime secrets:

- `API_SECRET_KEY`
- `API_DB_NAME`
- `API_DB_USER`
- `API_DB_PASSWORD`
- `API_DB_HOST`

Common optional API runtime values:

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
- `API_SLACK_REDIRECT_URI`

Keep Azure identifiers that are safe to print as environment variables. Keep credentials, client IDs, tenant IDs, subscription IDs, database URLs, Redis URLs, Slack secrets, JWT secrets, and SMTP secrets as GitHub Environment secrets or Azure Key Vault secrets.

## First Azure Bootstrap

Before the GitHub workflows can create resources, create an Azure subscription and an Entra ID app registration/service principal for GitHub Actions OIDC. Configure one federated credential per protected environment/branch policy, then store the resulting Azure IDs in the matching GitHub Environment secrets.

Recommended order:

1. Create or choose an Azure subscription.
2. Create a resource group for Terraform remote state.
3. Create an Azure Storage Account and Blob container for Terraform state.
4. Create an Entra app registration/service principal for GitHub Actions OIDC.
5. Add federated credentials for `dev`, `staging`, and `prod` GitHub Environments.
6. Add `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID` to each GitHub Environment.
7. Run the `IaC` workflow with `action=plan`.
8. Run the `IaC` workflow with `action=apply` after reviewing the plan.
9. Copy Terraform outputs for the ACR name, login server, API URL, and frontend URL into GitHub Environment variables.
10. Set `VITE_API_URL` and `VITE_WS_URL` from the API URL.
11. Run the `Container Release` workflow for the target environment with an immutable image tag.
12. Run the `IaC` workflow again with `action=apply` and the same image tag.

## Local Commands

```bash
terraform -chdir=deploy/terraform/environments/dev init
terraform -chdir=deploy/terraform/environments/dev plan
terraform -chdir=deploy/terraform/environments/dev apply
```

For staging or production, run the same commands with `environments/staging` or `environments/prod`. Production applies should happen through the protected GitHub Actions `IaC` workflow.

## GitHub Actions Flow

Use the `IaC` workflow first. It selects the matching Terraform environment folder from the `environment` input and supports `plan` or `apply`.

Use the `Container Release` workflow after the Azure Container Registry exists. It builds backend and frontend Docker images and can optionally push them to the selected environment registry.

Normal update flow:

1. Choose a new immutable image tag, for example `dev-005`.
2. Run `Container Release` with that tag and `push_images=true`.
3. Run `IaC` with the same `image_tag` and `action=apply`.
4. Confirm Azure Container Apps active revisions use that tag.

The `IaC` workflow writes two generated files during the run:

- `runtime.auto.tfvars.json`: API runtime secrets and optional settings from GitHub Environments.
- `zz-workflow.auto.tfvars.json`: workflow-controlled values such as `image_tag`.

The second file intentionally sorts after `terraform.tfvars` so workflow input wins over checked-in defaults. Do not put `image_tag` in `terraform.tfvars.example`; use the workflow input instead.

## Image Tags

Use immutable tags for deployments:

```text
dev-005
staging-014
prod-2026-06-16-1
<short-commit-sha>
```

Avoid deploying `dev-latest` through Terraform. It is useful as a moving registry pointer, but it is poor for auditability and rollback.

## Container App Outputs

After apply, Terraform prints:

- `container_registry_name`
- `container_registry_login_server`
- `container_apps_environment_id`
- `api_container_app_url`
- `frontend_container_app_url`

Use the API URL to populate `VITE_API_URL` and derive `VITE_WS_URL` by replacing `https://` with `wss://`.

## Remote State

The starter files use local state so development is simple. Before running staging or production applies, configure an Azure Storage backend in each environment:

```hcl
backend "azurerm" {
  resource_group_name  = "opssight-tfstate-rg"
  storage_account_name = "opssighttfstate"
  container_name       = "tfstate"
  key                  = "prod.terraform.tfstate"
}
```

Create the backend storage once, then enable the backend block and run `terraform init -migrate-state`.
