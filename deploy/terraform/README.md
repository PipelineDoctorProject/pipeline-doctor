# Terraform Infrastructure

Terraform is the source of truth for cloud infrastructure. It should create and own Azure resources such as the resource group, Azure Container Registry, Log Analytics, and the Container Apps environment.

Application runtime settings, image promotion, and verification can be handled after infrastructure exists. Keep secrets in GitHub Environments, Azure Key Vault, or the target platform secret store. Do not commit real secrets in Terraform variables.

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
9. Copy Terraform outputs for the ACR name and login server into GitHub Environment variables.
10. Run the `Container Release` workflow for the target environment.

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

## Remote State

The starter files use local state so development is simple. Before running production applies, configure an Azure Storage backend in each environment:

```hcl
backend "azurerm" {
  resource_group_name  = "opssight-tfstate-rg"
  storage_account_name = "opssighttfstate"
  container_name       = "tfstate"
  key                  = "prod.terraform.tfstate"
}
```

Create the backend storage once, then enable the backend block and run `terraform init -migrate-state`.
