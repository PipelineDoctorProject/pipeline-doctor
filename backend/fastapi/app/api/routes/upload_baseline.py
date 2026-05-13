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
)

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
        .order_by(Baseline.created_at.desc())
        .all()
    )
    models = db.query(MLModel)

    results = []

    for baseline in baselines:

        results.append({
            "id": baseline.id,
            "model_id": baseline.model_id,
            "version": baseline.version,
            "status": baseline.status,
            "is_active": baseline.is_active,
            "created_at": baseline.created_at,
            "schema": baseline.schema,
            "profile": baseline.profile,
        })

    return results


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

    # ==========================================
    # SAVE BASELINE VERSION
    # ==========================================
    baseline = create_baseline_version(
        db,
        model_id,
        baseline_data["schema"],
        baseline_data["profile"]
    )

    # ==========================================
    # RESPONSE
    # ==========================================
    return {
        "message": "Baseline created",
        **baseline
    }