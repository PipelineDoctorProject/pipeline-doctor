from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import os
import uuid

from app.db.session import get_db
from app.models.baseline import Baseline
from app.services.quality.baseline import create_baseline
from app.config.settings import BASELINE_UPLOAD_DIR

router = APIRouter(tags=["Data Quality Findings"])


@router.post("/baseline/upload")
async def upload_baseline(
    model_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # -------------------------
    # 1. Validate file
    # -------------------------
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    # -------------------------
    # 2. Save file
    # -------------------------
    file_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(BASELINE_UPLOAD_DIR, file_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # -------------------------
    # 3. Read CSV
    # -------------------------
    try:
        df = pd.read_csv(file_path)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV format")

    # -------------------------
    # 4. Basic validation (IMPORTANT)
    # -------------------------
    if df.shape[0] < 10:
        raise HTTPException(status_code=400, detail="Dataset too small")

    if df.isnull().mean().mean() > 0.5:
        raise HTTPException(status_code=400, detail="Too many null values")

    # -------------------------
    # 5. Create baseline
    # -------------------------
    baseline_data = create_baseline(df)

    # -------------------------
    # 6. Store in DB
    # -------------------------
    baseline = Baseline(
        model_id=model_id,
        file_path=file_path,
        schema=baseline_data["schema"],
        profile=baseline_data["profile"]
    )

    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # -------------------------
    # 7. Response
    # -------------------------
    return {
        "message": "Baseline uploaded successfully",
        "baseline_id": baseline.id,
        "columns": list(df.columns)
    }