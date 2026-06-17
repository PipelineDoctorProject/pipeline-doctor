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
- FastAPI API Container App
- Frontend Container App
- Celery worker Container App
- Celery beat Container App, one replica
- MLflow Container App
- Azure Cache for Redis
- Azure PostgreSQL Flexible Server for MLflow metadata
- Azure Blob Storage for MLflow artifacts
- Azure Blob Storage for application uploads, cleaned data, reports, and exports
- Optional Airflow webserver/scheduler Container Apps with Terraform-managed Airflow PostgreSQL metadata

One-shot migration jobs, Key Vault references, custom domains,
and advanced deployment slots should be added in the next infrastructure phase
after remote Terraform state is configured.

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
| Application database | Supabase production Postgres | Keep the current Supabase database. Use SSL, backups, migration control, and separate staging/prod projects. |
| Redis | Azure Cache for Redis | Use `rediss://` and TLS port `6380`. |
| MLflow | Azure Container Apps | Uses the backend image with a dedicated MLflow command. Keep it private if possible. |
| MLflow metadata DB | Azure Database for PostgreSQL Flexible Server | Managed by Terraform and kept separate from the application Supabase database. |
| MLflow artifacts | Azure Blob Storage | Managed by Terraform as a private container. |
| Application artifacts | Azure Blob Storage | Managed by Terraform as a private container for uploads, cleaned outputs, reports, and exports. |
| Secrets | Azure Key Vault / Container App secrets | Never bake secrets into images or committed env files. |
| Airflow | Azure Container Apps or managed Airflow/customer orchestrator | Terraform can deploy the built-in Airflow image for prod; production Airflow should not depend on a local Docker volume. |

## Production Deployment Flow

1. Create Azure subscription, GitHub OIDC credentials, and Terraform remote state.
2. Run the GitHub Actions `IaC` workflow with `action=plan`.
3. Review the Terraform plan and run `action=apply`.
4. Save Terraform ACR and Container App URL outputs into GitHub Environment values.
5. Set `VITE_API_URL` and `VITE_WS_URL` for the frontend build.
6. Run the GitHub Actions `Container Release` workflow with a new immutable image tag.
7. Run the GitHub Actions `IaC` workflow again with `action=apply` and the same image tag.
8. Confirm the active Azure Container App revisions use that image tag.
9. Keep the application database on Supabase and configure `API_DB_*` secrets.
10. Run `alembic upgrade head` once as a migration job.
11. Run `python scripts/repair_tenant_schemas.py` in that migration job.
12. Add `MLFLOW_POSTGRESQL_ADMIN_PASSWORD` as a GitHub Environment secret.
13. Leave `MLFLOW_BACKEND_STORE_URI` and `MLFLOW_ARTIFACT_ROOT` unset unless intentionally overriding the Terraform-managed MLflow PostgreSQL/Blob resources.
14. Configure Slack OAuth redirect URL to the public API callback.
15. Configure `AIRFLOW_CONN_OPSSIGHT_API` with a service token.
16. Trigger a staging DAG run with explicit model and input artifact.

## Build Images

The preferred path is the GitHub Actions `Container Release` workflow. It can
build images for `dev`, `staging`, or `prod` and optionally push to the selected
environment's Azure Container Registry.

For manual local testing from the repository root:

```powershell
docker build -t <acr>.azurecr.io/opssight-api:<tag> ./backend/fastapi
docker build -t <acr>.azurecr.io/opssight-airflow:<tag> ./airflow-setup
docker build `
  --build-arg VITE_API_URL=https://<api-domain> `
  --build-arg VITE_WS_URL=wss://<api-domain> `
  -f frontend/Dockerfile `
  -t <acr>.azurecr.io/opssight-frontend:<tag> .
docker push <acr>.azurecr.io/opssight-api:<tag>
docker push <acr>.azurecr.io/opssight-airflow:<tag>
docker push <acr>.azurecr.io/opssight-frontend:<tag>
```

## Provision Container Apps

Use the GitHub Actions `IaC` workflow and Terraform module for the current API, frontend, worker, beat, MLflow, Redis, and optional Airflow resources.

The Bicep template remains a reference for manual experiments:

```powershell
az deployment group create `
  --resource-group <resource-group> `
  --template-file deploy/azure/container-apps.bicep `
  --parameters @deploy/azure/container-apps.parameters.example.json
```

For real production, pass sensitive values from Azure Key Vault or CI/CD secrets instead of committing a filled parameter file.

## Image Promotion

Use the same immutable image tag in both workflows:

```text
Container Release: image_tag=dev-005, push_images=true
IaC:               image_tag=dev-005, action=apply
```

After deploy, verify in Azure Portal:

```text
Container App -> Application -> Revisions and replicas
Container App -> Application -> Containers -> Image tag
```

If the portal dropdown shows `dev-latest` by default, check the active revision and the container details for that revision. The dropdown lists all ACR tags and may default to `dev-latest` while browsing; the running revision is what matters.

For production, prefer managed identity plus `AcrPull` on ACR. The dev environment may use ACR admin credentials if the GitHub Actions service principal cannot create Azure role assignments.

## Current Service Mapping

| Local Compose service | Azure target |
|---|---|
| `redis` | Azure Cache for Redis |
| `celery-worker` | Azure Container App |
| `celery-beat` | Azure Container App, one replica |
| `mlflow` | Azure Container App |
| `mlflow-db` | Azure PostgreSQL Flexible Server managed by Terraform |
| `mlflow-artifacts` | Azure Blob Storage managed by Terraform |
| `uploads`, `cleaned`, `reports`, `exports` | Azure Blob Storage managed by Terraform |
| `airflow-webserver` | Azure Container App when `enable_airflow=true` |
| `airflow-scheduler` | Azure Container App when `enable_airflow=true` |
| `airflow-db` | Azure PostgreSQL Flexible Server managed by Terraform when `enable_airflow=true` |

The application database remains Supabase and is configured only through `API_DB_*` secrets.

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

For the current Container App flow, set `VITE_API_URL` and `VITE_WS_URL` in the GitHub Environment before running `Container Release`. Re-run `IaC` with the same tag after the image is pushed.

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
- Verify uploads, cleaned datasets, quarantine files, reports, and exports are written to the Terraform-managed app artifact container.
- Validate Slack public distribution for multi-workspace installation.
- Validate Terraform plans against the final Azure account, image registry, and DNS names before first production rollout.

## Remaining Hardening Work

The current codebase is ready for a strong staging deployment, but a final production cut should still add:

- Key Vault references or CI/CD secret injection for every sensitive parameter.
- Service-token based Airflow auth if you do not want Airflow to use admin credentials.
- Terraform-managed one-shot migration job resources.
- Application Insights instrumentation and structured JSON logs.
- Separate staging and production Slack apps or redirect URLs.
