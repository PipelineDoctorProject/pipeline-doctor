from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import os
import uuid
from app.dependencies.auth import require_tenant_user
from app.db.session import get_db
from app.services.quality.pipeline import run_data_quality_pipeline
from app.models.data_quality import DataQualityFinding
from app.models.baseline import Baseline
from app.schemas.data_quality import DataQualityResponse
from app.schemas.explanations import InsightExplanationResponse
from app.services.quality.data_loader import load_dataset
from app.services.ai_explanations import build_data_quality_explanation

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])

UPLOAD_DIR = "uploads/incoming"


async def save_upload(file: UploadFile) -> str:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV allowed")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")

    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    return file_path


def infer_model_from_active_baselines(db: Session, file_path: str):
    df = load_dataset(file_path)
    incoming_cols = {str(col).lower() for col in df.columns}

    baselines = (
        db.query(Baseline)
        .filter(
            Baseline.is_active == True,
            Baseline.status == "approved",
        )
        .all()
    )

    candidates = []

    for baseline in baselines:
        expected_cols = {str(col).lower() for col in (baseline.schema or {}).keys()}
        if not expected_cols:
            continue

        missing_cols = sorted(expected_cols - incoming_cols)
        extra_cols = sorted(incoming_cols - expected_cols)
        overlap = len(expected_cols & incoming_cols)
        score = overlap - (len(missing_cols) * 2) - (len(extra_cols) * 0.25)

        candidates.append({
            "model_id": baseline.model_id,
            "baseline_id": baseline.id,
            "baseline_version": baseline.version,
            "score": score,
            "matched_columns": overlap,
            "missing_columns": missing_cols,
            "extra_columns": extra_cols,
        })

    candidates.sort(key=lambda item: item["score"], reverse=True)

    if not candidates or candidates[0]["matched_columns"] == 0:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "No active model baseline matches the incoming schema.",
                "candidates": candidates[:5],
            },
        )

    best = candidates[0]
    tied = [
        candidate for candidate in candidates[1:]
        if candidate["score"] == best["score"]
    ]

    if tied:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Incoming schema matches multiple models. Send model_id explicitly.",
                "candidates": [best, *tied],
            },
        )

    return best

@router.get("/", response_model=list[DataQualityResponse])
def list_data_quality_findings(
    model_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    query = db.query(DataQualityFinding)
    if model_id is not None:
        query = query.filter(DataQualityFinding.model_id == model_id)
    return query.order_by(DataQualityFinding.id.desc()).all()


@router.post("/validate")
async def validate_data(
    model_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    file_path = await save_upload(file)

    result = run_data_quality_pipeline(db, model_id, file_path)

    return result


@router.post("/validate-auto")
async def validate_data_auto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    file_path = await save_upload(file)
    match = infer_model_from_active_baselines(db, file_path)
    result = run_data_quality_pipeline(db, match["model_id"], file_path)

    return {
        "matched_model_id": match["model_id"],
        "matched_baseline_id": match["baseline_id"],
        "match_score": match["score"],
        "result": result,
    }


@router.get("/explain", response_model=InsightExplanationResponse)
def explain_data_quality_run(
    run_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    findings = (
        db.query(DataQualityFinding)
        .filter(DataQualityFinding.pipeline_run_id == run_id)
        .order_by(DataQualityFinding.id.asc())
        .all()
    )

    if not findings:
        raise HTTPException(status_code=404, detail="No data quality findings found for this run")

    return build_data_quality_explanation(run_id, findings)
