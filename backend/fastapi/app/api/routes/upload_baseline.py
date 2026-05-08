from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import os
import uuid

from app.db.session import get_db
from app.models.baseline import Baseline
from app.services.quality.baseline import create_baseline,crea
from app.services.quality.baseline_service import create_baseline_version
from app.config.settings import BASELINE_UPLOAD_DIR

router = APIRouter(tags=["Data Quality Findings"])


@router.post("/baseline/upload")
async def upload_baseline(
    model_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV allowed")

    file_path = os.path.join(BASELINE_UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")

    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    df = pd.read_csv(file_path)

    if df.shape[0] < 10:
        raise HTTPException(status_code=400, detail="Too small dataset")

    baseline_data = create_baseline(df)

    baseline = create_baseline_version(
        db,
        model_id,
        baseline_data["schema"],
        baseline_data["profile"]
    )

    return {
        "message": "Baseline created (draft)",
        "version": baseline.version
    }