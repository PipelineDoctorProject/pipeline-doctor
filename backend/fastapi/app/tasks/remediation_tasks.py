from datetime import datetime

from celery.utils.log import get_task_logger

from app.core.celery_app import celery
from app.db.session import SessionLocal
from app.models.incident import Incident
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun
from app.models.remediation_action_log import RemediationActionLog
from app.models.remediation_run import RemediationRun
from app.models.tenant import Tenant
from app.services.remediation import decide_remediation
from app.services.remediation.retraining_service import run_retraining
from app.utils.schema_utils import set_schema

logger = get_task_logger(__name__)


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 1},
)
def run_remediation_task(
    self,
    remediation_run_id: int,
    tenant_id: str | None,
    target_column: str,
):
    db = SessionLocal()

    try:
        if tenant_id:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant and tenant.schema_name:
                set_schema(db, tenant.schema_name)

        remediation_run = (
            db.query(RemediationRun)
            .filter(RemediationRun.id == remediation_run_id)
            .first()
        )
        if not remediation_run:
            raise ValueError(f"Remediation run {remediation_run_id} was not found.")

        incident = db.query(Incident).filter(Incident.id == remediation_run.incident_id).first()
        if not incident:
            raise ValueError(f"Incident {remediation_run.incident_id} was not found.")

        pipeline_run = db.query(PipelineRun).filter(PipelineRun.id == remediation_run.run_id).first()
        if not pipeline_run:
            raise ValueError(f"Pipeline run {remediation_run.run_id} was not found.")

        model_record = db.query(MLModel).filter(MLModel.id == pipeline_run.model_id).first()
        if not model_record:
            raise ValueError(f"Model {pipeline_run.model_id} was not found.")

        policy = decide_remediation(
            {
                "severity": incident.severity,
                "failure_types": _extract_failure_types(incident.description),
            }
        )
        if not policy.get("allowed_to_execute") or policy.get("manual_only"):
            remediation_run.status = "blocked"
            remediation_run.result_summary = policy.get("reason")
            remediation_run.finished_at = datetime.utcnow()
            db.add(
                RemediationActionLog(
                    remediation_run_id=remediation_run.id,
                    step_name="policy_check",
                    status="blocked",
                    message=policy.get("reason") or "Remediation was blocked by policy.",
                    payload=policy,
                )
            )
            db.commit()
            return

        remediation_run.status = "running"
        remediation_run.started_at = datetime.utcnow()
        db.add(
            RemediationActionLog(
                remediation_run_id=remediation_run.id,
                step_name="start",
                status="running",
                message="Approved remediation execution started.",
                payload={"target_column": target_column},
            )
        )
        db.commit()

        result = run_retraining(
            db=db,
            run_id=remediation_run.run_id,
            model_id=model_record.id,
            target_column=target_column,
        )

        remediation_run.status = "completed"
        remediation_run.finished_at = datetime.utcnow()
        remediation_run.result_summary = f"Retraining completed with metrics: {result['metrics']}"
        db.add(
            RemediationActionLog(
                remediation_run_id=remediation_run.id,
                step_name="retraining",
                status="completed",
                message="Retraining completed successfully.",
                payload=result,
            )
        )
        db.commit()

    except Exception as exc:
        logger.error("Remediation task failed: %s", exc, exc_info=True)
        remediation_run = locals().get("remediation_run")
        if remediation_run:
            remediation_run.status = "failed"
            remediation_run.finished_at = datetime.utcnow()
            remediation_run.result_summary = str(exc)
            db.add(
                RemediationActionLog(
                    remediation_run_id=remediation_run.id,
                    step_name="failure",
                    status="failed",
                    message="Remediation execution failed.",
                    payload={"error": str(exc)},
                )
            )
            db.commit()
        raise
    finally:
        db.close()


def _extract_failure_types(description: str) -> list[str]:
    import json

    try:
        payload = json.loads(description or "")
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, dict):
        return []

    return payload.get("failure_types") or []
