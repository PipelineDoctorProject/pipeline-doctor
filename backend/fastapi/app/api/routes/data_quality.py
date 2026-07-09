from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
import uuid
from app.dependencies.auth import require_tenant_user
from app.db.session import get_db
from app.models.data_quality import DataQualityFinding
from app.models.baseline import Baseline
from app.schemas.data_quality import DataQualityResponse
from app.schemas.pagination import PaginatedResponse
from app.schemas.explanations import InsightExplanationResponse
from app.services.quality.data_loader import load_dataset
from app.services.ai_explanations import build_data_quality_explanation
from app.services.access_control import require_accessible_model
from app.services.file_storage import store_upload

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])

UPLOAD_DIR = "uploads/incoming"

async def save_upload(file: UploadFile) -> str:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV allowed")

    return await store_upload(file, f"{UPLOAD_DIR}/{uuid.uuid4()}_{file.filename}")


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


@router.get("/", response_model=PaginatedResponse[DataQualityResponse])
def list_data_quality_findings(
    model_id: int | None = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    if model_id is not None:
        require_accessible_model(db, model_id, current_user.tenant_id)

    runs_query = db.query(DataQualityFinding.pipeline_run_id).distinct()
    if model_id is not None:
        runs_query = runs_query.filter(DataQualityFinding.model_id == model_id)
        
    total_count = runs_query.count()
    
    # Get paginated run ids
    paginated_runs = runs_query.order_by(DataQualityFinding.pipeline_run_id.desc()).offset(skip).limit(limit).all()
    run_ids = [r[0] for r in paginated_runs]
    
    items = []
    if run_ids:
        items = db.query(DataQualityFinding).filter(DataQualityFinding.pipeline_run_id.in_(run_ids)).order_by(DataQualityFinding.id.desc()).all()
    
    passed_checks = db.query(func.count(DataQualityFinding.id)).filter(DataQualityFinding.success == True)
    failed_checks = db.query(func.count(DataQualityFinding.id)).filter(DataQualityFinding.success == False)
    total_runs_query = db.query(func.count(distinct(DataQualityFinding.pipeline_run_id)))
    
    if model_id is not None:
        passed_checks = passed_checks.filter(DataQualityFinding.model_id == model_id)
        failed_checks = failed_checks.filter(DataQualityFinding.model_id == model_id)
        total_runs_query = total_runs_query.filter(DataQualityFinding.model_id == model_id)
        
    stats = {
        "passed_checks": passed_checks.scalar() or 0,
        "failed_checks": failed_checks.scalar() or 0,
        "total_runs": total_runs_query.scalar() or 0,
    }
    
    return {
        "items": items,
        "total_count": total_count,
        "stats": stats
    }


@router.post("/validate")
async def validate_data(
    model_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    from app.services.quality.pipeline import run_data_quality_pipeline

    require_accessible_model(db, model_id, current_user.tenant_id)

    file_path = await save_upload(file)

    result = run_data_quality_pipeline(
        db,
        model_id,
        file_path,
        current_tenant_id=current_user.tenant_id,
    )

    return result


@router.post("/validate-auto")
async def validate_data_auto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    from app.services.quality.pipeline import run_data_quality_pipeline

    file_path = await save_upload(file)
    match = infer_model_from_active_baselines(db, file_path)
    result = run_data_quality_pipeline(
        db,
        match["model_id"],
        file_path,
        current_tenant_id=current_user.tenant_id,
    )

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
