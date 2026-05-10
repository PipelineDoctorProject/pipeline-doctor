from sqlalchemy.orm import Session
from app.models.pipeline_run import PipelineRun


def create_pipeline_run(db: Session, model_id: int, baseline_version: int, file_path: str):
    run = PipelineRun(
        model_id=model_id,
        baseline_version=baseline_version,
        file_path=file_path,
        status="running"
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def update_pipeline_run_status(db: Session, run_id: int, status: str):
    run = db.get(PipelineRun, run_id)

    if not run:
        raise Exception("Pipeline run not found")

    run.status = status
    db.commit()