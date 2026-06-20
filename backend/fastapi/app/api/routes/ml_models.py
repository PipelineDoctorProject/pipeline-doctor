from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Depends
)

from sqlalchemy.orm import Session

from typing import List

from app.config.settings import resolve_mlflow_tracking_uri
from app.db.session import get_db

from app.models.ml_model import MLModel

from app.dependencies.auth import require_tenant_user


from app.schemas.ml_model import (
    MLModelCreate,
    MLModelResponse,
    DiscoverModelsRequest,
    ModelVersionsRequest,
    SetModelAliasRequest
)
from app.services.access_control import require_accessible_model

router = APIRouter(
    prefix="/ml-models",
    tags=["ML Models"]
)


def _default_registry_status(model: MLModel):
    if not model.mlflow_model_name:
        return {
            "registry_status": "local_only",
            "registry_message": "This model is registered only in Pipeline Doctor."
        }

    return {
        "registry_status": "available",
        "registry_message": "MLflow registry metadata is configured for this model."
    }


def _mlflow_registry_status(model: MLModel):
    from mlflow.tracking import MlflowClient

    if not model.mlflow_model_name:
        return _default_registry_status(model)

    try:
        client = MlflowClient(
            tracking_uri=resolve_mlflow_tracking_uri(model.mlflow_tracking_uri)
        )

        if model.version:
            version = client.get_model_version(
                name=model.mlflow_model_name,
                version=str(model.version)
            )
            return {
                "registry_status": "available",
                "registry_message": f"MLflow version {version.version} is available."
            }

        client.get_registered_model(model.mlflow_model_name)
        return {
            "registry_status": "available",
            "registry_message": "MLflow registered model is available."
        }

    except Exception as exc:
        return {
            "registry_status": "missing",
            "registry_message": f"MLflow registry lookup failed: {exc}"
        }


def _serialize_model(model: MLModel, include_live_registry_status: bool = False):
    data = {
        "id": model.id,
        "name": model.name,
        "version": model.version,
        "framework": model.framework,
        "mlflow_model_name": model.mlflow_model_name,
        "mlflow_alias": model.mlflow_alias,
        "mlflow_run_id": model.mlflow_run_id,
        "mlflow_tracking_uri": model.mlflow_tracking_uri,
        "expected_features": model.expected_features,
        "created_at": model.created_at,
    }
    if include_live_registry_status:
        data.update(_mlflow_registry_status(model))
    else:
        data.update(_default_registry_status(model))
    return data


# =====================================================
# LIST MODELS
# =====================================================
@router.get("/", response_model=List[MLModelResponse])
def list_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    models = (
        db.query(MLModel)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Keep the list endpoint fast and independent from live MLflow availability.
    return [_serialize_model(model) for model in models]


# =====================================================
# REGISTER MODEL
# =====================================================
@router.post(
    "/",
    response_model=MLModelResponse
)
def register_model(
    model_in: MLModelCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    db_model = MLModel(
        tenant_id=current_user.tenant_id,
        name=model_in.name,
        version=model_in.version,
        framework=model_in.framework,
        mlflow_model_name=model_in.mlflow_model_name,
        mlflow_alias=model_in.mlflow_alias,
        mlflow_run_id=model_in.mlflow_run_id,
        mlflow_tracking_uri=model_in.mlflow_tracking_uri,
        expected_features=model_in.expected_features
    )

    db.add(db_model)

    db.commit()

    db.refresh(db_model)

    return db_model

# GET SINGLE MODEL
# =====================================================
@router.get(
    "/{model_id}",
    response_model=MLModelResponse
)
def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    db_model = (
        db.query(MLModel)
        .filter(MLModel.id == model_id)
        .first()
    )

    if not db_model:
        raise HTTPException(
            status_code=404,
            detail="Model not found"
        )

    return _serialize_model(
        db_model,
        include_live_registry_status=True
    )


# =====================================================
# DISCOVER REGISTERED MODELS
# =====================================================
@router.post("/discover")
def discover_models(
    data: DiscoverModelsRequest,
    current_user=Depends(require_tenant_user)
):
    from mlflow.tracking import MlflowClient

    try:

        client = MlflowClient(
            tracking_uri=resolve_mlflow_tracking_uri(data.tracking_uri)
        )

        registered_models = list(
            client.search_registered_models()
        )

        models = []

        for model in registered_models:

            models.append({
                "name": model.name
            })

        return {
            "models": models
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# =====================================================
# GET MODEL VERSIONS
# =====================================================
@router.post("/versions")
def get_model_versions(
    data: ModelVersionsRequest,
    current_user=Depends(require_tenant_user)
):
    from mlflow.tracking import MlflowClient

    try:
        client = MlflowClient(
            tracking_uri=resolve_mlflow_tracking_uri(data.tracking_uri)
        )

        versions = client.search_model_versions(
            f"name='{data.model_name}'"
        )

        # Retrieve registered model to compile version-to-alias mapping
        version_to_aliases = {}
        try:
            rm = client.get_registered_model(data.model_name)
            if rm and hasattr(rm, "aliases") and rm.aliases:
                for alias_name, ver in rm.aliases.items():
                    version_to_aliases.setdefault(str(ver), []).append(alias_name)
        except Exception:
            pass

        version_data = []
        for version in versions:
            obj_aliases = getattr(version, "aliases", []) or []
            v_aliases = version_to_aliases.get(str(version.version), [])
            combined_aliases = list(set(list(obj_aliases) + v_aliases))

            artifacts_exist = True
            try:
                # Determine the version source to pick the right check strategy.
                # - "models:/m-xxx" sources are registry model copies → blobs live in Azure
                #   under the models/ prefix and can be checked directly.
                # - "runs:/RUN_ID/..." sources are run-artifact references. The Celery
                #   retraining worker logs artifacts to the container's local mlartifacts
                #   directory, not to Azure Blob Storage. Listing blobs for these will
                #   always return 0, causing a false "Artifacts Missing" warning.
                #   Instead, trust that MLflow's successful registration means artifacts exist.
                version_source = getattr(version, "source", "") or ""

                if version_source.startswith("runs:/"):
                    # Run-based registration: trust the MLflow registration status.
                    # If MLflow accepted the version, the model file exists on the server.
                    version_status = str(getattr(version, "status", "") or "").upper()
                    artifacts_exist = version_status != "FAILED_REGISTRATION"
                else:
                    # Registry model copy (models:/m-xxx or wasbs:// direct source):
                    # verify the blobs are physically present in Azure Storage.
                    download_uri = client.get_model_version_download_uri(data.model_name, str(version.version))
                    resolved_uri = download_uri

                    if resolved_uri.startswith("wasbs://") or resolved_uri.startswith("wasb://"):
                        import os
                        from urllib.parse import urlparse
                        from azure.storage.blob import BlobServiceClient

                        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
                        if connection_string:
                            parsed = urlparse(resolved_uri)
                            container = parsed.username or parsed.netloc.split("@")[0]
                            path_prefix = parsed.path.lstrip("/")

                            service_client = BlobServiceClient.from_connection_string(connection_string)
                            container_client = service_client.get_container_client(container)

                            blobs = container_client.list_blobs(name_starts_with=path_prefix)
                            has_blobs = False
                            for _ in blobs:
                                has_blobs = True
                                break
                            if not has_blobs:
                                artifacts_exist = False
                        else:
                            # No connection string — fall back to MLflow artifact listing
                            if version.run_id:
                                artifacts = client.list_artifacts(version.run_id)
                                if not artifacts:
                                    artifacts_exist = False
                            else:
                                artifacts_exist = False
                    else:
                        # Non-Azure URI (file:// or local dev path)
                        if version.run_id:
                            artifacts = client.list_artifacts(version.run_id)
                            if not artifacts:
                                artifacts_exist = False
                        else:
                            artifacts_exist = False
            except Exception as e:
                import logging
                logging.getLogger(__name__).exception(f"Artifact check failed for version {version.version}: {e}")
                artifacts_exist = False

            version_data.append({
                "version": version.version,
                "stage": version.current_stage,
                "run_id": version.run_id,
                "aliases": combined_aliases,
                "artifacts_exist": artifacts_exist
            })

        return {
            "versions": version_data
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )



# =====================================================
# UPDATE MODEL ALIAS / ROLLBACK
# =====================================================
@router.post("/{model_id}/set-alias")
def set_model_alias(
    model_id: int,
    data: SetModelAliasRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    from mlflow.tracking import MlflowClient

    db_model = require_accessible_model(db, model_id, current_user.tenant_id)

    if not db_model.mlflow_model_name:
        raise HTTPException(
            status_code=400,
            detail="Model is not configured for MLflow registry."
        )

    try:
        client = MlflowClient(
            tracking_uri=resolve_mlflow_tracking_uri(db_model.mlflow_tracking_uri)
        )
        client.set_registered_model_alias(
            name=db_model.mlflow_model_name,
            alias=data.alias,
            version=str(data.version)
        )

        db_model.version = str(data.version)
        db_model.mlflow_run_id = data.run_id
        db_model.mlflow_alias = data.alias
        db.commit()
        db.refresh(db_model)

        return _serialize_model(db_model, include_live_registry_status=True)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update model alias: {e}"
        )
