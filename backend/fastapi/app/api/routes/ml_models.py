from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Depends
)

from sqlalchemy.orm import Session

from typing import List

from mlflow.tracking import MlflowClient

from app.models.ml_model import MLModel

from app.dependencies.auth import require_tenant_user


from app.schemas.ml_model import (
    MLModelCreate,
    MLModelResponse,
    DiscoverModelsRequest,
    ModelVersionsRequest
)

router = APIRouter(
    prefix="/ml-models",
    tags=["ML Models"]
)


def _mlflow_registry_status(model: MLModel):
    if not model.mlflow_model_name:
        return {
            "registry_status": "local_only",
            "registry_message": "This model is registered only in Pipeline Doctor."
        }

    try:
        client = MlflowClient(
            tracking_uri=model.mlflow_tracking_uri
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


def _serialize_model(model: MLModel):
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
    data.update(_mlflow_registry_status(model))
    return data


# =====================================================
# LIST MODEL
# =====================================================
@router.get("/", response_model=List[MLModelResponse])
def list_models(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(require_tenant_user)
):

    db: Session = request.state.db

    if not db:
        raise HTTPException(
            status_code=401,
            detail="Tenant database not found"
        )

    models = (
        db.query(MLModel)
        .offset(skip)
        .limit(limit)
        .all()
    )

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
    request: Request,
    current_user=Depends(require_tenant_user)
):

    db: Session = request.state.db

    if not db:
        raise HTTPException(
            status_code=401,
            detail="Tenant database not found"
        )

    db_model = MLModel(
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


# =====================================================
# LIST MODELS
# =====================================================
@router.get(
    "/",
    response_model=List[MLModelResponse]
)
def list_models(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(require_tenant_user)
):

    db: Session = request.state.db

    if not db:
        raise HTTPException(
            status_code=401,
            detail="Tenant database not found"
        )

    models = (
        db.query(MLModel)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [_serialize_model(model) for model in models]


# =====================================================
# GET SINGLE MODEL
# =====================================================
@router.get(
    "/{model_id}",
    response_model=MLModelResponse
)
def get_model(
    model_id: int,
    request: Request,
    current_user=Depends(require_tenant_user)
):

    db: Session = request.state.db

    if not db:
        raise HTTPException(
            status_code=401,
            detail="Tenant database not found"
        )

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

    return _serialize_model(db_model)


# =====================================================
# DISCOVER REGISTERED MODELS
# =====================================================
@router.post("/discover")
def discover_models(
    data: DiscoverModelsRequest,
    current_user=Depends(require_tenant_user)
):

    try:

        client = MlflowClient(
            tracking_uri=data.tracking_uri
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

    try:

        client = MlflowClient(
            tracking_uri=data.tracking_uri
        )

        versions = client.search_model_versions(
            f"name='{data.model_name}'"
        )

        version_data = []

        for version in versions:

            version_data.append({
                "version": version.version,
                "stage": version.current_stage,
                "run_id": version.run_id
            })

        return {
            "versions": version_data
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
