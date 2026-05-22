import json
from datetime import datetime, timezone

import redis
from sqlalchemy import text
from celery.utils.log import get_task_logger

from app.config.settings import REDIS_URL
from app.core.celery_app import celery
from app.db.session import SessionLocal

from app.models.agent_run import AgentRun
from app.models.ml_model import MLModel   # ✅ FIXED
from app.models.pipeline_run import PipelineRun
from app.models.tenant import Tenant
from app.tasks.ai_tasks import run_doctor_agent_task
from app.utils.schema_utils import set_schema

logger = get_task_logger(__name__)


def _set_public_schema(db):
    db.info.pop("schema_name", None)
    db.execute(text("SET search_path TO public"))


@celery.task
def record_beat_heartbeat():
    """
    Stores a lightweight heartbeat so the API can verify that Celery Beat
    is actively dispatching scheduled tasks.
    """
    payload = {
        "task": "record_beat_heartbeat",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        client.set("celery:beat:last_heartbeat", json.dumps(payload))
        logger.info("Recorded Celery Beat heartbeat")
    finally:
        client.close()


@celery.task
def trigger_doctor_monitoring():

    db = SessionLocal()

    try:
        logger.info("🚀 Starting Doctor monitoring sweep")

        _set_public_schema(db)
        tenants = db.query(Tenant).all()

        for tenant in tenants:
            if not tenant.schema_name:
                continue

            set_schema(db, tenant.schema_name)

            latest_run = (
                db.query(PipelineRun)
                .join(MLModel, PipelineRun.model_id == MLModel.id)
                .filter(MLModel.tenant_id == tenant.id)
                .order_by(PipelineRun.created_at.desc())
                .first()
            )

            if not latest_run:
                continue

            existing_run = (
                db.query(AgentRun)
                .filter(
                    AgentRun.pipeline_run_id == latest_run.id,
                    AgentRun.agent_name == "doctor",
                )
                .order_by(AgentRun.id.desc())
                .first()
            )

            if existing_run and existing_run.status in {"running", "completed"}:
                continue

            run_doctor_agent_task.apply_async(
                args=(latest_run.id, tenant.id, "doctor"),
                expires=300,
            )

            logger.info(
                f"📡 Triggered RCA for tenant={tenant.id}, run={latest_run.id}"
            )

        logger.info("✅ Monitoring sweep completed")

    finally:
        try:
            _set_public_schema(db)
        except Exception:
            pass
        db.close()
