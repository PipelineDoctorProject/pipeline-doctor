from datetime import datetime

from billiard.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger

from app.config import settings
from app.core.celery_app import celery
from app.db.session import SessionLocal
from app.models.incident import Incident
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun
from app.models.remediation_action_log import RemediationActionLog
from app.models.remediation_run import RemediationRun
from app.models.tenant import Tenant
from app.services.remediation.reporting import sync_incident_remediation_state
from app.services.remediation import decide_remediation
from app.services.remediation.retraining_service import RemediationCanceled
from app.utils.schema_utils import set_schema

logger = get_task_logger(__name__)


@celery.task(
    bind=True,
    soft_time_limit=settings.REMEDIATION_TASK_SOFT_TIME_LIMIT_SECONDS,
    time_limit=settings.REMEDIATION_TASK_TIME_LIMIT_SECONDS,
)
def run_remediation_task(
    self,
    remediation_run_id: int,
    tenant_id: str | None,
    target_column: str | None,
):
    from app.services.remediation.retraining_service import run_retraining

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

        if remediation_run.status == "rejected":
            logger.info("Remediation run %s was rejected before execution started.", remediation_run.id)
            return

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
            sync_incident_remediation_state(
                db,
                incident,
                remediation_run,
                status="blocked",
                message=policy.get("reason"),
            )
            db.commit()
            return

        if _mark_canceled_if_requested(db, remediation_run, incident, stage="before_start"):
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
        sync_incident_remediation_state(
            db,
            incident,
            remediation_run,
            status="running",
            message="Approved remediation execution started.",
            target_column=target_column,
        )
        db.commit()

        result = run_retraining(
            db=db,
            run_id=remediation_run.run_id,
            model_id=model_record.id,
            target_column=target_column,
            should_cancel=lambda: _is_cancel_requested(db, remediation_run.id),
        )

        if _mark_canceled_if_requested(
            db,
            remediation_run,
            incident,
            stage="after_training",
            result=result,
        ):
            return

        remediation_run.status = "pending_promotion"
        remediation_run.finished_at = datetime.utcnow()
        remediation_run.result_summary = (
            "Candidate retraining completed successfully and is awaiting promotion review."
        )
        db.add(
            RemediationActionLog(
                remediation_run_id=remediation_run.id,
                step_name="retraining",
                status="pending_promotion",
                message="Retraining completed successfully.",
                payload=result,
            )
        )
        sync_incident_remediation_state(
            db,
            incident,
            remediation_run,
            status="pending_promotion",
            message=remediation_run.result_summary,
            result=result,
            target_column=target_column,
        )
        db.commit()

    except RemediationCanceled as exc:
        remediation_run = locals().get("remediation_run")
        incident = locals().get("incident")
        if remediation_run:
            remediation_run.status = "canceled"
            remediation_run.finished_at = datetime.utcnow()
            remediation_run.result_summary = str(exc)
            db.add(
                RemediationActionLog(
                    remediation_run_id=remediation_run.id,
                    step_name="canceled",
                    status="canceled",
                    message="Remediation execution was canceled.",
                    payload={"reason": str(exc)},
                )
            )
            if incident:
                sync_incident_remediation_state(
                    db,
                    incident,
                    remediation_run,
                    status="canceled",
                    message=str(exc),
                )
            db.commit()
    except SoftTimeLimitExceeded as exc:
        logger.error("Remediation task exceeded its soft time limit.", exc_info=True)
        remediation_run = locals().get("remediation_run")
        incident = locals().get("incident")
        if remediation_run:
            remediation_run.status = "failed"
            remediation_run.finished_at = datetime.utcnow()
            remediation_run.result_summary = (
                "Remediation timed out while loading artifacts or training the candidate model."
            )
            db.add(
                RemediationActionLog(
                    remediation_run_id=remediation_run.id,
                    step_name="timeout",
                    status="failed",
                    message=remediation_run.result_summary,
                    payload={"error": str(exc)},
                )
            )
            if incident:
                sync_incident_remediation_state(
                    db,
                    incident,
                    remediation_run,
                    status="failed",
                    message=remediation_run.result_summary,
                )
            db.commit()
        raise
    except Exception as exc:
        logger.error("Remediation task failed: %s", exc, exc_info=True)
        remediation_run = locals().get("remediation_run")
        incident = locals().get("incident")
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
            if incident:
                sync_incident_remediation_state(
                    db,
                    incident,
                    remediation_run,
                    status="failed",
                    message=str(exc),
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


def _is_cancel_requested(db, remediation_run_id: int) -> bool:
    db.expire_all()
    remediation_run = (
        db.query(RemediationRun)
        .filter(RemediationRun.id == remediation_run_id)
        .first()
    )
    if not remediation_run:
        return False

    return remediation_run.status in {"cancel_requested", "rejected", "canceled"}


def _mark_canceled_if_requested(
    db,
    remediation_run: RemediationRun,
    incident: Incident,
    *,
    stage: str,
    result: dict | None = None,
) -> bool:
    if not _is_cancel_requested(db, remediation_run.id):
        return False

    db.refresh(remediation_run)
    remediation_run.status = "canceled"
    remediation_run.finished_at = datetime.utcnow()
    remediation_run.result_summary = "Remediation execution was canceled before candidate promotion."
    db.add(
        RemediationActionLog(
            remediation_run_id=remediation_run.id,
            step_name=stage,
            status="canceled",
            message=remediation_run.result_summary,
            payload=result,
        )
    )
    sync_incident_remediation_state(
        db,
        incident,
        remediation_run,
        status="canceled",
        message=remediation_run.result_summary,
        result=result,
    )
    db.commit()
    return True
