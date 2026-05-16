from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import uuid
from app.dependencies.auth import require_tenant_user
from app.db.session import get_db
from app.services.quality.pipeline import run_data_quality_pipeline
from app.models.data_quality import DataQualityFinding
from app.schemas.data_quality import DataQualityResponse

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])

UPLOAD_DIR = "uploads/incoming"

@router.get("/", response_model=list[DataQualityResponse])
def list_data_quality_findings(db: Session = Depends(get_db), current_user=Depends(require_tenant_user)):
    return db.query(DataQualityFinding).order_by(DataQualityFinding.id.desc()).all()


@router.post("/validate")
async def validate_data(
    model_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    # 1. Validate file
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV allowed")

    # 2. Save file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")

    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    # 3. Run pipeline
    result = run_data_quality_pipeline(db, model_id, file_path)

    return result