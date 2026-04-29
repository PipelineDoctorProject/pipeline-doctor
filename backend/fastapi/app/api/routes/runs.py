from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pipeline_run import PipelineRun
from app.schemas.run import RunCreate, RunResponse,PipeLineCreate,PipeLineResponse
from app.services.runs.pipeline_runner import run_pipeline
router = APIRouter(prefix="/runs", tags=["Runs"])


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


# @router.get("/", response_model=list[RunResponse])
# def list_runs_api(db: Session = Depends(get_db)):
#     runs = db.query(PipelineRun).order_by(PipelineRun.id.desc()).all()

#     return [
#         {
#             "id": run.id,
#             "status": run.status,
#             "drift_score": run.drift_score,
#             "created_at": run.started_at,
#         }
#         for run in runs
#     ]
    
    
@router.post('/start', response_model=PipeLineResponse)
def fake_pipeline_create(data: PipeLineCreate, db: Session = Depends(get_db)):
    run = run_pipeline(db, data.model_id, mode=data.mode)

    return {
        "id": run.id,
        "model_id": run.model_id,
        "status": run.status,
        "started_at": run.started_at
    }
