from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Request,
    Depends
    
)

from sqlalchemy.orm import Session

import pandas as pd
import os
import uuid

from app.models.baseline import Baseline
from app.models.ml_model import MLModel
from app.dependencies.auth import require_tenant_user

from app.services.quality.baseline import (
    create_baseline,
)

from app.services.quality.baseline_service import (
    create_baseline_version,
    activate_baseline,
)
from app.services.access_control import require_accessible_model

from app.config.settings import (
    BASELINE_UPLOAD_DIR,
)

router = APIRouter(
    tags=["Baselines"]
)

# =====================================================
# LIST BASELINES
# =====================================================
@router.get("/baselines/")
def get_baselines(
    request: Request,
    current_user=Depends(require_tenant_user)

):

    db: Session = request.state.db

    if not db:
        raise HTTPException(
            status_code=401,
            detail="Tenant database not found"
        )

    baselines = (
        db.query(Baseline)
        .order_by(
            Baseline.created_at.desc()
        )
        .all()
    )

    results = []

    for baseline in baselines:

        # ==========================================
        # GET MODEL
        # ==========================================
        model = (
            db.query(MLModel)
            .filter(
                MLModel.id == baseline.model_id
            )
            .first()
        )

        results.append({
            "id": baseline.id,

            "model_id": baseline.model_id,

            "model_name": (
                model.name
                if model
                else "Unknown Model"
            ),

            "version": baseline.version,

            "status": baseline.status,

            "is_active": baseline.is_active,

            "created_at": baseline.created_at,

            "schema": baseline.schema,

            "profile": baseline.profile,
        })

    return results


# =====================================================
# ACTIVATE BASELINE
# =====================================================
@router.patch("/baselines/{baseline_id}/activate")
def activate_baseline_route(
    baseline_id: int,
    request: Request
):

    db: Session = request.state.db

    if not db:
        raise HTTPException(
            status_code=401,
            detail="Tenant database not found"
        )

    try:
        baseline = activate_baseline(
            db,
            baseline_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    model = (
        db.query(MLModel)
        .filter(
            MLModel.id == baseline.model_id
        )
        .first()
    )

    return {
        "id": baseline.id,
        "model_id": baseline.model_id,
        "model_name": (
            model.name
            if model
            else "Unknown Model"
        ),
        "version": baseline.version,
        "status": baseline.status,
        "is_active": baseline.is_active,
        "created_at": baseline.created_at,
        "schema": baseline.schema,
        "profile": baseline.profile,
    }


# =====================================================
# UPLOAD BASELINE
# =====================================================
@router.post("/baseline/upload")
async def upload_baseline(
    request: Request,
    model_id: int,
    file: UploadFile = File(...),
    current_user=Depends(require_tenant_user)
):

    db: Session = request.state.db

    if not db:
        raise HTTPException(
            status_code=401,
            detail="Tenant database not found"
        )

    require_accessible_model(db, model_id, current_user.tenant_id)

    # ==========================================
    # VALIDATE FILE
    # ==========================================
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV allowed"
        )

    # ==========================================
    # CREATE DIRECTORY
    # ==========================================
    os.makedirs(
        BASELINE_UPLOAD_DIR,
        exist_ok=True
    )

    # ==========================================
    # SAVE FILE
    # ==========================================
    file_path = os.path.join(
        BASELINE_UPLOAD_DIR,
        f"{uuid.uuid4()}_{file.filename}"
    )

    with open(file_path, "wb") as buffer:

        while chunk := await file.read(
            1024 * 1024
        ):
            buffer.write(chunk)

    # ==========================================
    # LOAD CSV
    # ==========================================
    try:

        df = pd.read_csv(file_path)

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid CSV file"
        )

    # ==========================================
    # VALIDATE DATASET SIZE
    # ==========================================
    if df.shape[0] < 10:

        raise HTTPException(
            status_code=400,
            detail="Too small dataset"
        )

    # ==========================================
    # CREATE BASELINE
    # ==========================================
    baseline_data = create_baseline(df)
    baseline_data["profile"]["_meta"] = {
        "source_file_path": file_path,
        "source_filename": file.filename,
    }

    # ==========================================
    # SAVE BASELINE VERSION
    # ==========================================
    try:
        baseline = create_baseline_version(
            db,
            model_id,
            baseline_data["schema"],
            baseline_data["profile"]
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create baseline: {exc}"
        ) from exc

    # ==========================================
    # RESPONSE
    # ==========================================
    return {
        "message": "Baseline created",
        "id": baseline.id,
        "model_id": baseline.model_id,
        "version": baseline.version,
        "status": baseline.status,
        "is_active": baseline.is_active,
        "created_at": str(baseline.created_at),
    }

