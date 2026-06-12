# Terraform Infrastructure

Terraform is the source of truth for cloud infrastructure. It should create and own Azure resources such as the resource group, Azure Container Registry, Log Analytics, and the Container Apps environment.

Application runtime settings, image promotion, and verification can be handled after infrastructure exists. Keep secrets in GitHub Environments, Azure Key Vault, or the target platform secret store. Do not commit real secrets in Terraform variables.

## Layout

- `environments/dev`: Development Azure infrastructure.
- `environments/prod`: Production Azure infrastructure.
- `modules/container_apps`: Reusable Azure Container Apps platform module.

## Local Commands

```bash
terraform -chdir=deploy/terraform/environments/dev init
terraform -chdir=deploy/terraform/environments/dev plan
terraform -chdir=deploy/terraform/environments/dev apply
```

For production, run the same commands with `environments/prod`. Production applies should happen through the protected GitHub Actions `IaC` workflow.

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
