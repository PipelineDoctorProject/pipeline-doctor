from datetime import datetime
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Query
import pandas as pd
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_tenant_user
from app.models.incident import Incident
from app.models.ml_model import MLModel
from app.models.remediation_action_log import RemediationActionLog
from app.models.pipeline_run import PipelineRun
from app.models.remediation_run import RemediationRun
from app.schemas.remediation import (
    RemediationActionLogResponse,
    RemediationContextResponse,
    RemediationDecisionResponse,
    RemediationRunResponse,
)
from app.services.remediation import decide_remediation
from app.services.remediation.reporting import sync_incident_remediation_state
from app.services.remediation.promotion_service import (
    approve_candidate_for_staging,
    confirm_candidate_deployment,
    get_candidate_result_for_run,
    get_staged_promotion_result_for_run,
)
from app.services.remediation.retraining_service import (
    collect_retraining_context,
    prepare_retraining_plan,
)
from app.tasks.remediation_tasks import run_remediation_task

router = APIRouter(prefix="/remediation", tags=["Remediation"])


@router.get("/incident/{incident_id}", response_model=list[RemediationRunResponse])
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


@router.get("/incident/{incident_id}/context", response_model=RemediationContextResponse)
def get_remediation_context(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    pipeline_run = db.query(PipelineRun).filter(PipelineRun.id == incident.run_id).first()
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")

    model_record = db.query(MLModel).filter(MLModel.id == pipeline_run.model_id).first()
    if not model_record:
        raise HTTPException(status_code=404, detail="ML model not found for remediation.")

    context = collect_retraining_context(
        db=db,
        pipeline_run=pipeline_run,
        model_record=model_record,
    )

    return {
        "incident_id": incident.id,
        "run_id": pipeline_run.id,
        "model_id": model_record.id,
        "model_name": model_record.name,
        "model_framework": model_record.framework,
        "expected_features": context["expected_features"],
        "expected_features_source": context["expected_features_source"],
        "dataset_columns": context["dataset_columns"],
        "training_mode": context["training_mode"],
        "target_required": context["target_required"],
        "target_candidates": context["target_candidates"],
        "suggested_target_column": context["suggested_target_column"],
        "cleaned_data_available": context["cleaned_data_available"],
        "readiness_warnings": context["readiness_warnings"],
    }


@router.get("/{remediation_run_id}", response_model=RemediationRunResponse)
def get_remediation_run(
    remediation_run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    remediation_run = (
        db.query(RemediationRun)
        .filter(RemediationRun.id == remediation_run_id)
        .first()
    )
    if not remediation_run:
        raise HTTPException(status_code=404, detail="Remediation run not found.")

    return remediation_run


@router.get("/{remediation_run_id}/logs", response_model=list[RemediationActionLogResponse])
def list_remediation_logs(
    remediation_run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    remediation_run = (
        db.query(RemediationRun)
        .filter(RemediationRun.id == remediation_run_id)
        .first()
    )
    if not remediation_run:
        raise HTTPException(status_code=404, detail="Remediation run not found.")

    return (
        db.query(RemediationActionLog)
        .filter(RemediationActionLog.remediation_run_id == remediation_run_id)
        .order_by(RemediationActionLog.created_at.asc())
        .all()
    )


@router.post("/incident/{incident_id}/approve", response_model=RemediationDecisionResponse)
def approve_retraining_for_incident(
    incident_id: int,
    target_column: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    from app.tasks.remediation_tasks import run_remediation_task

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can approve remediation.")

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    pipeline_run = db.query(PipelineRun).filter(PipelineRun.id == incident.run_id).first()
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")

    model_record = db.query(MLModel).filter(MLModel.id == pipeline_run.model_id).first()
    if not model_record:
        raise HTTPException(status_code=404, detail="ML model not found for remediation.")

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

    _validate_retraining_preconditions(
        db=db,
        pipeline_run=pipeline_run,
        model_record=model_record,
        target_column=target_column,
    )

    existing_active_run = (
        db.query(RemediationRun)
        .filter(
            RemediationRun.incident_id == incident.id,
            RemediationRun.status.in_(
                ["approved", "queued", "running", "cancel_requested", "pending_promotion", "staged"]
            ),
        )
        .order_by(RemediationRun.id.desc())
        .first()
    )
    if existing_active_run:
        raise HTTPException(
            status_code=409,
            detail=(
                "A remediation run is already active for this incident. "
                f"Existing run id={existing_active_run.id}, status={existing_active_run.status}."
            ),
        )

    remediation_run = RemediationRun(
        incident_id=incident.id,
        run_id=pipeline_run.id,
        tenant_id=current_user.tenant_id,
        action_type=policy.get("action_type", "retrain_model"),
        status="queued",
        trigger_mode="manual_approval",
        created_by=current_user.email,
    )
    db.add(remediation_run)
    db.commit()
    db.refresh(remediation_run)
    db.add(
        RemediationActionLog(
            remediation_run_id=remediation_run.id,
            step_name="approval",
            status="approved",
            message=f"Remediation approved by {current_user.email} and queued for execution.",
            payload={"target_column": target_column},
        )
    )
    sync_incident_remediation_state(
        db,
        incident,
        remediation_run,
        status="queued",
        message="Remediation was approved and queued for execution.",
        target_column=target_column,
    )
    db.commit()

    run_remediation_task.delay(remediation_run.id, current_user.tenant_id, target_column)

    return {
        "id": remediation_run.id,
        "status": remediation_run.status,
        "action_type": remediation_run.action_type,
        "message": "Retraining remediation approved and queued.",
    }


@router.post("/{remediation_run_id}/reject", response_model=RemediationDecisionResponse)
def reject_remediation_run(
    remediation_run_id: int,
    review_notes: str | None = None,
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

    if remediation_run.status in {
        "failed",
        "blocked",
        "rejected",
        "canceled",
        "staged",
        "deployed",
        "promoted",
        "promotion_rejected",
    }:
        raise HTTPException(
            status_code=409,
            detail=f"Remediation run is already in terminal status '{remediation_run.status}'.",
        )

    if remediation_run.status == "cancel_requested":
        raise HTTPException(
            status_code=409,
            detail="Cancellation has already been requested for this remediation run.",
        )

    incident = db.query(Incident).filter(Incident.id == remediation_run.incident_id).first()
    review_message_suffix = f" Notes: {review_notes}" if review_notes else ""

    if remediation_run.status in {"pending_promotion", "completed", "staged"}:
        remediation_run.status = "promotion_rejected"
        remediation_run.result_summary = (
            f"Candidate promotion/deployment rejected by {current_user.email}.{review_message_suffix}"
        ).strip()
        db.add(
            RemediationActionLog(
                remediation_run_id=remediation_run.id,
                step_name="promotion_review",
                status="promotion_rejected",
                message=remediation_run.result_summary,
                payload={"review_notes": review_notes},
            )
        )
        if incident:
            sync_incident_remediation_state(
                db,
                incident,
                remediation_run,
                status="promotion_rejected",
                message=remediation_run.result_summary,
                result={"review_notes": review_notes},
            )
        db.commit()
        return {
            "id": remediation_run.id,
            "status": remediation_run.status,
            "action_type": remediation_run.action_type,
            "message": remediation_run.result_summary,
        }

    if remediation_run.status == "running":
        remediation_run.status = "cancel_requested"
        remediation_run.result_summary = f"Cancellation requested by {current_user.email}"
        db.add(
            RemediationActionLog(
                remediation_run_id=remediation_run.id,
                step_name="cancellation_request",
                status="cancel_requested",
                message=remediation_run.result_summary,
                payload=None,
            )
        )
        if incident:
            sync_incident_remediation_state(
                db,
                incident,
                remediation_run,
                status="cancel_requested",
                message=remediation_run.result_summary,
            )
    else:
        remediation_run.status = "rejected"
        remediation_run.finished_at = datetime.utcnow()
        remediation_run.result_summary = f"Rejected by {current_user.email}"
        db.add(
            RemediationActionLog(
                remediation_run_id=remediation_run.id,
                step_name="rejection",
                status="rejected",
                message=remediation_run.result_summary,
                payload=None,
            )
        )
        if incident:
            sync_incident_remediation_state(
                db,
                incident,
                remediation_run,
                status="rejected",
                message=remediation_run.result_summary,
            )
    db.commit()

    return {
        "id": remediation_run.id,
        "status": remediation_run.status,
        "action_type": remediation_run.action_type,
        "message": remediation_run.result_summary,
    }


@router.post("/{remediation_run_id}/promote", response_model=RemediationDecisionResponse)
def promote_remediation_candidate(
    remediation_run_id: int,
    review_notes: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can stage remediation candidates.")

    remediation_run = (
        db.query(RemediationRun)
        .filter(RemediationRun.id == remediation_run_id)
        .first()
    )
    if not remediation_run:
        raise HTTPException(status_code=404, detail="Remediation run not found.")

    if remediation_run.status not in {"pending_promotion", "completed"}:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only remediation runs with a completed candidate can be staged. "
                f"Current status is '{remediation_run.status}'."
            ),
        )

    incident = db.query(Incident).filter(Incident.id == remediation_run.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    pipeline_run = db.query(PipelineRun).filter(PipelineRun.id == remediation_run.run_id).first()
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")

    model_record = db.query(MLModel).filter(MLModel.id == pipeline_run.model_id).first()
    if not model_record:
        raise HTTPException(status_code=404, detail="ML model not found for promotion.")

    candidate_result = get_candidate_result_for_run(db, remediation_run.id)
    if not candidate_result:
        raise HTTPException(
            status_code=409,
            detail="Candidate artifacts could not be found for this remediation run.",
        )

    try:
        promotion_result = approve_candidate_for_staging(
            db=db,
            model_record=model_record,
            candidate_result=candidate_result,
            promoted_by=current_user.email,
            review_notes=review_notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    remediation_run.status = "staged"
    remediation_run.result_summary = (
        "Candidate approved for staging"
        f" alias '{promotion_result['staged_alias']}'"
        f" by {current_user.email}."
    )
    db.add(
        RemediationActionLog(
            remediation_run_id=remediation_run.id,
            step_name="staging_approval",
            status="staged",
            message=remediation_run.result_summary,
            payload=promotion_result,
        )
    )
    sync_incident_remediation_state(
        db,
        incident,
        remediation_run,
        status="staged",
        message=remediation_run.result_summary,
        result=promotion_result,
    )
    db.commit()

    return {
        "id": remediation_run.id,
        "status": remediation_run.status,
        "action_type": remediation_run.action_type,
        "message": remediation_run.result_summary,
    }


@router.post("/{remediation_run_id}/confirm-deployment", response_model=RemediationDecisionResponse)
def confirm_remediation_candidate_deployment(
    remediation_run_id: int,
    deployment_notes: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can confirm candidate deployment.")

    remediation_run = (
        db.query(RemediationRun)
        .filter(RemediationRun.id == remediation_run_id)
        .first()
    )
    if not remediation_run:
        raise HTTPException(status_code=404, detail="Remediation run not found.")

    if remediation_run.status != "staged":
        raise HTTPException(
            status_code=409,
            detail=(
                "Only staged remediation candidates can be marked deployed. "
                f"Current status is '{remediation_run.status}'."
            ),
        )

    incident = db.query(Incident).filter(Incident.id == remediation_run.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    pipeline_run = db.query(PipelineRun).filter(PipelineRun.id == remediation_run.run_id).first()
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")

    model_record = db.query(MLModel).filter(MLModel.id == pipeline_run.model_id).first()
    if not model_record:
        raise HTTPException(status_code=404, detail="ML model not found for deployment confirmation.")

    promotion_result = get_staged_promotion_result_for_run(db, remediation_run.id)
    if not promotion_result:
        raise HTTPException(
            status_code=409,
            detail="Staged candidate metadata could not be found for this remediation run.",
        )

    try:
        deployment_result = confirm_candidate_deployment(
            db=db,
            model_record=model_record,
            promotion_result=promotion_result,
            deployed_by=current_user.email,
            deployment_notes=deployment_notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    remediation_run.status = "deployed"
    remediation_run.finished_at = datetime.utcnow()
    remediation_run.result_summary = (
        "Candidate deployment confirmed and champion alias updated"
        f" by {current_user.email}."
    )
    db.add(
        RemediationActionLog(
            remediation_run_id=remediation_run.id,
            step_name="deployment_confirmation",
            status="deployed",
            message=remediation_run.result_summary,
            payload=deployment_result,
        )
    )
    sync_incident_remediation_state(
        db,
        incident,
        remediation_run,
        status="deployed",
        message=remediation_run.result_summary,
        result=deployment_result,
    )
    db.commit()

    return {
        "id": remediation_run.id,
        "status": remediation_run.status,
        "action_type": remediation_run.action_type,
        "message": "Candidate staged. Deploy the staging alias, then confirm deployment to update champion.",
    }


def _extract_failure_types(description: str) -> list[str]:
    try:
        payload = json.loads(description or "")
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, dict):
        return []

    return payload.get("failure_types") or []


def _validate_retraining_preconditions(
    db: Session,
    pipeline_run: PipelineRun,
    model_record: MLModel,
    target_column: str | None,
) -> None:
    try:
        prepare_retraining_plan(
            db=db,
            pipeline_run=pipeline_run,
            model_record=model_record,
            target_column=target_column,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
