from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_tenant_user
from app.models.incident import Incident
from app.models.pipeline_run import PipelineRun
from app.models.remediation_run import RemediationRun
from app.services.remediation import decide_remediation
from app.tasks.remediation_tasks import run_remediation_task

router = APIRouter(prefix="/remediation", tags=["Remediation"])


@router.get("/incident/{incident_id}")
def list_remediation_runs_for_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    return (
        db.query(RemediationRun)
        .filter(RemediationRun.incident_id == incident_id)
        .order_by(RemediationRun.id.desc())
        .all()
    )


@router.post("/incident/{incident_id}/approve")
def approve_retraining_for_incident(
    incident_id: int,
    target_column: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can approve remediation.")

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    pipeline_run = db.query(PipelineRun).filter(PipelineRun.id == incident.run_id).first()
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")

    failure_types = _extract_failure_types(incident.description)
    policy = decide_remediation(
        {
            "severity": incident.severity,
            "failure_types": failure_types,
        }
    )

    if not policy.get("allowed_to_execute") or policy.get("manual_only"):
        raise HTTPException(
            status_code=400,
            detail=policy.get("reason") or "This incident is not eligible for retraining.",
        )

    remediation_run = RemediationRun(
        incident_id=incident.id,
        run_id=pipeline_run.id,
        tenant_id=current_user.tenant_id,
        action_type=policy.get("action_type", "retrain_model"),
        status="approved",
        trigger_mode="manual_approval",
        created_by=current_user.email,
        started_at=datetime.utcnow(),
    )
    db.add(remediation_run)
    db.commit()
    db.refresh(remediation_run)

    run_remediation_task.delay(remediation_run.id, current_user.tenant_id, target_column)

    return {
        "id": remediation_run.id,
        "status": remediation_run.status,
        "action_type": remediation_run.action_type,
        "message": "Retraining remediation approved and queued.",
    }


@router.post("/{remediation_run_id}/reject")
def reject_remediation_run(
    remediation_run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can reject remediation.")

    remediation_run = (
        db.query(RemediationRun)
        .filter(RemediationRun.id == remediation_run_id)
        .first()
    )
    if not remediation_run:
        raise HTTPException(status_code=404, detail="Remediation run not found.")

    remediation_run.status = "rejected"
    remediation_run.finished_at = datetime.utcnow()
    remediation_run.result_summary = f"Rejected by {current_user.email}"
    db.commit()

    return {
        "id": remediation_run.id,
        "status": remediation_run.status,
        "message": remediation_run.result_summary,
    }


def _extract_failure_types(description: str) -> list[str]:
    try:
        payload = json.loads(description or "")
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, dict):
        return []

    return payload.get("failure_types") or []
