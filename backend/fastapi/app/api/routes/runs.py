from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_tenant_user
from app.models.pipeline_run import PipelineRun
from app.schemas.pagination import PaginatedRunsResponse
from app.schemas.run import RunCreate, RunResponse, PipeLineCreate, PipeLineResponse
from app.services import file_storage

router = APIRouter(prefix="/runs", tags=["Runs"])

@router.get("/", response_model=PaginatedRunsResponse[RunResponse])
def list_runs(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    """List pipeline runs for the current tenant's models."""
    query = (
        db.query(PipelineRun)
        .join(PipelineRun.model)
        .filter(PipelineRun.model.has(tenant_id=current_user.tenant_id))
    )
    total_count = query.count()
    runs = query.order_by(PipelineRun.id.asc()).offset(skip).limit(limit).all()
    
    return {
        "runs": runs,
        "total_count": total_count
    }

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

    if not file_storage.exists(run.cleaned_data_path):
        raise HTTPException(
            status_code=404,
            detail="Cleaned data file not found for this run. The pipeline may not have completed successfully."
        )

    return StreamingResponse(
        file_storage.open_binary(run.cleaned_data_path),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="cleaned_run_{run_id}.csv"'},
    )
