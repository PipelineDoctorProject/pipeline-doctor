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
    updated = (
        db.query(PipelineRun)
        .filter(PipelineRun.id == run_id)
        .update({"status": status}, synchronize_session=False)
    )

    if not updated:
        raise Exception("Pipeline run not found")

    db.commit()


def update_pipeline_run_fields(db: Session, run_id: int, **fields):
    updated = (
        db.query(PipelineRun)
        .filter(PipelineRun.id == run_id)
        .update(fields, synchronize_session=False)
    )

    if not updated:
        raise Exception("Pipeline run not found")

    db.commit()
