# Azure Production Deployment

This folder describes the recommended Azure deployment shape for OpsSight.

Terraform in `../terraform` is now the preferred infrastructure-as-code path.
The Bicep files in this folder remain as useful Azure Container Apps references
and can still be used manually if needed.

The current Terraform module provisions the first Azure foundation:

- Resource group
- Log Analytics workspace
- Azure Container Apps environment
- Azure Container Registry

Application Container Apps, managed databases, Redis, Blob Storage, Key Vault
references, domains, and deployment slots should be added in the next
infrastructure phase after the Azure account, GitHub OIDC, and remote Terraform
state are configured.

The key production rule is:

```text
Build once, run migrations once, deploy API/worker/frontend separately,
and keep secrets, databases, queues, and artifacts outside app containers.
```

## Recommended Azure Architecture

| Layer | Azure service | Notes |
|---|---|---|
| Frontend | Azure Static Web Apps or Azure Container Apps | Static Web Apps is simplest. Container Apps works when you want one containerized deployment model. |
| API | Azure Container Apps | Run the FastAPI image with `uvicorn` only. Do not run migrations inside every API replica. |
| Worker | Azure Container Apps | Same backend image, different command for Celery worker. |
| Beat scheduler | Azure Container Apps | Same backend image, Celery beat command. Keep one replica. |
| Database | Supabase production Postgres or Azure Database for PostgreSQL Flexible Server | Use SSL, backups, migration control, and separate staging/prod databases. |
| Redis | Azure Cache for Redis | Use `rediss://` and TLS port `6380`. |
| MLflow | Azure Container Apps or managed ML platform | Use managed Postgres backend and durable artifact storage. Keep it private if possible. |
| Artifacts | Azure Blob Storage | Store uploads, cleaned outputs, reports, and MLflow artifacts durably. |
| Secrets | Azure Key Vault / Container App secrets | Never bake secrets into images or committed env files. |
| Airflow | Managed Airflow, Astronomer, AKS, or customer orchestrator | Production Airflow should not depend on a local Docker volume. |

## Production Deployment Flow

1. Create Azure subscription, GitHub OIDC credentials, and Terraform remote state.
2. Run the GitHub Actions `IaC` workflow with `action=plan`.
3. Review the Terraform plan and run `action=apply`.
4. Save Terraform ACR outputs into GitHub Environment variables.
5. Run the GitHub Actions `Container Release` workflow for the target environment.
6. Create production database, Redis, Blob Storage, and Key Vault-backed secrets.
7. Add all backend environment variables as Container App secrets.
8. Run `alembic upgrade head` once as a migration job.
9. Run `python scripts/repair_tenant_schemas.py` in that migration job.
10. Deploy API app from the backend image.
11. Deploy Celery worker app from the backend image.
12. Deploy Celery beat as a single-replica app from the backend image.
13. Deploy frontend with `VITE_API_URL` and `VITE_WS_URL` pointing to the public API host.
14. Configure Slack OAuth redirect URL to the public API callback.
15. Configure Airflow `opssight_api` connection with a service token.
16. Trigger a staging DAG run with explicit model and input artifact.

## Build Images

The preferred path is the GitHub Actions `Container Release` workflow. It can
build images for `dev`, `staging`, or `prod` and optionally push to the selected
environment's Azure Container Registry.

For manual local testing from the repository root:

```powershell
docker build -t <acr>.azurecr.io/opssight-api:<tag> ./backend/fastapi
docker build `
  --build-arg VITE_API_URL=https://<api-domain> `
  --build-arg VITE_WS_URL=wss://<api-domain> `
  -f frontend/Dockerfile `
  -t <acr>.azurecr.io/opssight-frontend:<tag> .
docker push <acr>.azurecr.io/opssight-api:<tag>
docker push <acr>.azurecr.io/opssight-frontend:<tag>
```

## Provision Container Apps

Use `container-apps.bicep` as the starting infrastructure template for the API, worker, beat, frontend, and Log Analytics workspace:

```powershell
az deployment group create `
  --resource-group <resource-group> `
  --template-file deploy/azure/container-apps.bicep `
  --parameters @deploy/azure/container-apps.parameters.example.json
```

For real production, pass sensitive values from Azure Key Vault or CI/CD secrets instead of committing a filled parameter file.

## Run Migrations

Run migrations as a release step before starting or scaling API replicas:

```bash
alembic upgrade head
python scripts/repair_tenant_schemas.py
```

In Azure Container Apps, use a one-off job using the same backend image and the production backend env.

Do not keep these commands in the API startup command in production. Multiple replicas can race each other and repeat tenant repair work.

## Runtime Commands

Use the same backend image with different commands:

```bash
# API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers

# Worker
celery -A app.core.celery_app:celery worker --loglevel=info --queues=ai,scheduler,emails,remediation --concurrency=2

# Beat
celery -A app.core.celery_app:celery beat --loglevel=info
```

## Airflow Production Contract

Airflow should send explicit model and batch inputs:

```json
{
  "model_name": "spotify-kmeans-recommender",
  "input_uri": "https://storage-account.blob.core.windows.net/batches/run-20260612.csv?<sas-token>"
}
```

Production Airflow should authenticate with OpsSight through a service token or scoped service account, not a personal admin password.

## Frontend Runtime

Vite values are public build-time configuration:

```env
VITE_API_URL=https://api.your-domain.com
VITE_WS_URL=wss://api.your-domain.com
```

If you use Azure Static Web Apps, set these as build environment variables. If you use the frontend Dockerfile, pass them as Docker build args.

## Production Readiness Gates

- Use HTTPS for frontend, API, Slack redirects, and WebSockets.
- Store all secrets in Key Vault or Container App secrets.
- Run migrations once per release.
- Verify tenant isolation on all list/detail endpoints.
- Configure DB backups and point-in-time restore.
- Configure Redis TLS.
- Add API health checks and Container App probes.
- Add central logging with Application Insights.
- Add alerting for API errors, worker failures, queue backlog, and failed DAG pushes.
- Move uploads/cleaned/report artifacts to durable object storage.
- Validate Slack public distribution for multi-workspace installation.
- Validate the Container Apps Bicep template against your final Azure account, image registry, and DNS names before first production rollout.

## Remaining Hardening Work

The current codebase is ready for a strong staging deployment, but a final production cut should still add:

- Azure Blob storage adapter for uploads, cleaned data, report exports, and MLflow artifacts.
- Key Vault references or CI/CD secret injection for every sensitive parameter.
- Service-token based Airflow auth if you do not want Airflow to use admin credentials.
- Deployment workflow that updates Container Apps after images are pushed.
- Application Insights instrumentation and structured JSON logs.
- Separate staging and production Slack apps or redirect URLs.
