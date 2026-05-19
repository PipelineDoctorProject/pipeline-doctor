from celery.utils.log import get_task_logger

from app.core.celery_app import celery
from app.db.session import SessionLocal

from app.models.ml_model import MLModel   # ✅ FIXED
from app.models.pipeline_run import PipelineRun
from app.tasks.ai_tasks import run_doctor_agent_task

logger = get_task_logger(__name__)


@celery.task
def trigger_doctor_monitoring():

    db = SessionLocal()

    try:
        logger.info("🚀 Starting Doctor monitoring sweep")

        models = db.query(MLModel).all()

        for model in models:

            latest_run = (
                db.query(PipelineRun)
                .filter(PipelineRun.model_id == model.id)
                .order_by(PipelineRun.created_at.desc())
                .first()
            )

            if not latest_run:
                continue

            if getattr(latest_run, "is_analyzed", False):
                continue

            run_doctor_agent_task.delay(
                latest_run.id,
                model.tenant_id,
                "doctor"
            )

            logger.info(
                f"📡 Triggered RCA for model={model.id}, run={latest_run.id}"
            )

        logger.info("✅ Monitoring sweep completed")

    finally:
        db.close()