from datetime import datetime
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_tenant_user
from app.models.pipeline_run import PipelineRun
from app.schemas.run import RunCreate, RunResponse, PipeLineCreate, PipeLineResponse

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("/{run_id}/download-cleaned")
def download_cleaned_data(
    run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    """Download the cleaned CSV file for a specific pipeline run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if not run.cleaned_data_path or not os.path.exists(run.cleaned_data_path):
        raise HTTPException(
            status_code=404,
            detail="Cleaned data file not found for this run. The pipeline may not have completed successfully."
        )

    return FileResponse(
        path=run.cleaned_data_path,
        media_type="text/csv",
        filename=f"cleaned_run_{run_id}.csv"
    )



# @router.post("/", response_model=RunResponse)
# def create_run_api(data: RunCreate, db: Session = Depends(get_db)):
#     run = PipelineRun(
#         model_id=1,
#         status=data.status,
#         drift_score=data.drift_score,
#         started_at=datetime.utcnow(),
#     )

#     db.add(run)
#     db.commit()
#     db.refresh(run)

#     return {
#         "id": run.id,
#         "status": run.status,
#         "drift_score": run.drift_score,
#         "created_at": run.started_at,
#     }


@router.get("/", response_model=list[RunResponse])
def list_runs_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    runs = db.query(PipelineRun).order_by(PipelineRun.id.desc()).all()
    return runs
    
# @router.post('/start', response_model=PipeLineResponse)
# def fake_pipeline_create(data: PipeLineCreate, db: Session = Depends(get_db)):
#     run = run_pipeline(db, data.model_id, mode=data.mode)

#     return {
#         "id": run.id,
#         "model_id": run.model_id,
#         "status": run.status,
#         "started_at": run.started_at
#     }
