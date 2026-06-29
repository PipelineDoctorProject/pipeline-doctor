from fastapi import APIRouter, Depends, HTTPException, Query
import json

from sqlalchemy.orm import Session, selectinload

from app.dependencies.auth import require_tenant_user
from app.db.session import get_db

from app.models.incident import Incident
from app.models.incident_group import IncidentGroup
from app.models.agent_run import AgentRun
from app.models.agent_step_log import AgentStepLog
from app.models.drift_finding import DriftFinding
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun
from app.services.incidents.grouping import attach_incident_to_group
from app.services.incidents.live_events import publish_incident_event
from app.services.slack_service import send_incident_notification
from app.services.access_control import require_accessible_model
from app.services.remediation import decide_remediation

from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
)

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)


@router.post("/", response_model=IncidentResponse)
def create_incident(
    data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):

    incident = Incident(
        run_id=data.run_id,
        title=data.title,
        description=data.description,
        failure_type=data.failure_type,
        severity=data.severity,
        status="open",
    )

    db.add(incident)
    db.flush()
    attach_incident_to_group(db, incident=incident)

    db.commit()

    db.refresh(incident)
    publish_incident_event("incident_created", incident)
    send_incident_notification(db, tenant_id=current_user.tenant_id, incident=incident)

    return incident


@router.get("/", response_model=list[IncidentResponse])
def list_incidents(
    model_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    if model_id is not None:
        require_accessible_model(db, model_id, current_user.tenant_id)

    return _serialized_incidents(
        db,
        model_id=model_id,
        tenant_id=current_user.tenant_id,
    )


@router.get("/filtered")
def filter_incidents(
    model_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    if model_id is not None:
        require_accessible_model(db, model_id, current_user.tenant_id)

    return _serialized_incidents(
        db,
        model_id=model_id,
        tenant_id=current_user.tenant_id,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):

    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:

        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    require_accessible_model(db, incident.run.model_id, current_user.tenant_id)

    drift_finding = None
    if incident.finding_type == "drift" and incident.finding_id:
        drift_finding = (
            db.query(DriftFinding)
            .filter(DriftFinding.id == incident.finding_id)
            .first()
        )

    return _serialize_incident(incident, drift_finding)


@router.get("/{incident_id}/agent-runs")
def get_incident_agent_runs(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):

    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:

        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    require_accessible_model(db, incident.run.model_id, current_user.tenant_id)

    runs = (
        db.query(AgentRun)
        .filter(
            AgentRun.pipeline_run_id == incident.run_id
        )
        .order_by(AgentRun.id.desc())
        .all()
    )

    return runs


@router.get("/{incident_id}/children", response_model=list[IncidentResponse])
def get_incident_children(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):

    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    require_accessible_model(db, incident.run.model_id, current_user.tenant_id)

    if not incident.group_id:
        return [_serialize_incident(incident)]

    grouped_incidents = (
        db.query(Incident)
        .filter(Incident.group_id == incident.group_id)
        .order_by(Incident.created_at.asc(), Incident.id.asc())
        .all()
    )

    drift_ids = [
        child.finding_id
        for child in grouped_incidents
        if child.finding_type == "drift" and child.finding_id
    ]
    drift_by_id: dict[int, DriftFinding] = {}
    if drift_ids:
        drift_by_id = {
            finding.id: finding
            for finding in db.query(DriftFinding)
            .filter(DriftFinding.id.in_(drift_ids))
            .all()
        }

    return [
        _serialize_incident(child, drift_by_id.get(child.finding_id))
        for child in grouped_incidents
    ]


@router.get("/agent-runs/{agent_run_id}/steps")
def get_agent_steps(
    agent_run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):

    steps = (
        db.query(AgentStepLog)
        .filter(
            AgentStepLog.agent_run_id == agent_run_id
        )
        .order_by(
            AgentStepLog.step_index.asc()
        )
        .all()
    )

    return steps


def _serialize_incident(
    incident: Incident,
    drift_finding: DriftFinding | None = None
):

    rca_report = _parse_rca_report(incident.description)
    final_report = _parse_final_report(rca_report)
    remediation = _derive_remediation_policy(
        incident,
        rca_report,
        final_report,
    )

    return {
        "id": incident.id,
        "run_id": incident.run_id,
        "title": incident.title,
        "description": _human_description(
            incident,
            rca_report
        ),
        "failure_type": incident.failure_type,
        "finding_type": incident.finding_type,
        "finding_id": incident.finding_id,
        "group_id": incident.group_id,
        "severity": incident.severity,
        "status": incident.status,
        "created_at": incident.created_at,
        "child_incident_count": len(incident.group.incidents) if incident.group else 1,
        "is_primary_incident": bool(
            incident.group and incident.group.primary_incident_id == incident.id
        ),
        "group_title": incident.group.title if incident.group else incident.title,
        "group_summary": incident.group.summary if incident.group else _human_description(incident, rca_report),
        "guidance": _build_guidance(
            incident,
            drift_finding,
            rca_report
        ),
        "rca_report": rca_report,
        "remediation": remediation,
        "final_report": final_report,
    }


def _serialized_incidents(
    db: Session,
    model_id: int | None = None,
    tenant_id: str | None = None,
):
    # NOTE: tenant isolation is already enforced at the DB schema level
    # (search_path is set to the tenant's schema by AuthMiddleware).
    # The extra MLModel.tenant_id filter was redundant and caused 0 results
    # because ml_models.tenant_id does not match the user UUID format.
    query = (
        db.query(IncidentGroup)
        .join(PipelineRun, IncidentGroup.run_id == PipelineRun.id)
        .join(MLModel, PipelineRun.model_id == MLModel.id)
        # Eagerly load group.incidents in ONE extra query (SELECT … WHERE group_id IN (…))
        # instead of issuing a separate lazy-load per group (N+1 problem → 20s timeout).
        .options(selectinload(IncidentGroup.incidents))
    )

    if model_id is not None:
        query = query.filter(PipelineRun.model_id == model_id)

    groups = query.order_by(IncidentGroup.created_at.desc(), IncidentGroup.id.desc()).all()

    representative_incidents = []
    for group in groups:
        representative = next(
            (incident for incident in group.incidents if incident.id == group.primary_incident_id),
            None,
        )
        if not representative and group.incidents:
            representative = sorted(
                group.incidents,
                key=lambda incident: (incident.created_at, incident.id),
                reverse=True,
            )[0]
        if representative:
            representative_incidents.append(representative)

    drift_ids = [
        incident.finding_id
        for incident in representative_incidents
        if incident.finding_type == "drift" and incident.finding_id
    ]

    drift_by_id: dict[int, DriftFinding] = {}

    if drift_ids:
        drift_by_id = {
            finding.id: finding
            for finding in db.query(DriftFinding)
            .filter(DriftFinding.id.in_(drift_ids))
            .all()
        }

    return [
        _serialize_incident(
            incident,
            drift_by_id.get(incident.finding_id)
        )
        for incident in representative_incidents
    ]


def _parse_rca_report(description: str):

    try:
        payload = json.loads(description or "")

        return payload if isinstance(payload, dict) else None

    except json.JSONDecodeError:
        return None


def _human_description(
    incident: Incident,
    rca_report: dict | None
):

    if not rca_report:
        return incident.description

    return rca_report.get("summary") or incident.description


def _build_guidance(
    incident: Incident,
    drift_finding: DriftFinding | None,
    rca_report: dict | None,
):

    if rca_report:

        provider = rca_report.get("provider") or "fallback"
        model = rca_report.get("model") or "deterministic-rules"

        return {
            "source": (
                "llm"
                if provider != "fallback"
                else "deterministic"
            ),
            "model": model,
            "cause": (
                rca_report.get("summary")
                or "The RCA engine grouped the run's failed monitoring signals."
            ),
            "action": (
                rca_report.get("recommendation")
                or "Review the evidence and fix the highest severity issue first."
            ),
        }

    if drift_finding:

        feature = drift_finding.feature_name or "feature"
        psi = drift_finding.psi_score or 0
        ks = drift_finding.ks_score or 0
        pvalue = drift_finding.ks_pvalue
        score = drift_finding.drift_score or 0

        strength = (
            "strong"
            if psi >= 0.3
            else "moderate"
            if psi >= 0.2
            else "minor"
        )

        statistical_note = (
            "KS p-value supports a statistically significant shift."
            if pvalue is not None and pvalue < 0.05
            else (
                "KS p-value is not significant, so confirm with "
                "business context before treating it as bad data."
            )
        )

        return {
            "source": "metric_interpreter",
            "model": None,
            "cause": (
                f"{feature} has {strength} drift: "
                f"PSI={psi:.4f}, "
                f"KS={ks:.4f}, "
                f"score={score:.4f}. "
                f"{statistical_note}"
            ),
            "action": (
                f"Compare {feature} in the current batch "
                "against the baseline window. "
                "Refresh the baseline only when the new "
                "population is expected; otherwise inspect "
                "the upstream feed."
            ),
        }

    return {
        "source": "metric_interpreter",
        "model": None,
        "cause": (
            "One or more monitoring signals crossed "
            "the incident threshold."
        ),
        "action": (
            "Review Data Quality and Drift details together "
            "before retraining or approving a new baseline."
        ),
    }


def _parse_remediation(
    rca_report: dict | None,
):
    if not rca_report:
        return None

    remediation = rca_report.get("remediation")
    return remediation if isinstance(remediation, dict) else None


def _derive_remediation_policy(
    incident: Incident,
    rca_report: dict | None,
    final_report: dict | None,
):
    stored_remediation = _parse_remediation(rca_report)
    failure_types = _extract_failure_types(rca_report, final_report)

    if not failure_types and incident.failure_type:
        failure_types = [incident.failure_type]

    if not failure_types:
        return stored_remediation

    policy = decide_remediation(
        {
            "severity": incident.severity,
            "failure_types": failure_types,
        }
    )

    if stored_remediation:
        merged_policy = {
            **stored_remediation,
            **policy,
        }
        return merged_policy

    return policy


def _extract_failure_types(
    rca_report: dict | None,
    final_report: dict | None,
) -> list[str]:
    candidate_sources = [
        rca_report,
        final_report,
    ]

    if isinstance(rca_report, dict):
        report = rca_report.get("report")
        if isinstance(report, dict):
            candidate_sources.append(report)

    for source in candidate_sources:
        if not isinstance(source, dict):
            continue

        failure_types = source.get("failure_types")
        if isinstance(failure_types, list):
            return [
                str(failure_type)
                for failure_type in failure_types
                if failure_type
            ]

    return []


def _parse_final_report(
    rca_report: dict | None,
):
    if not rca_report:
        return None

    final_report = rca_report.get("final_report")
    return final_report if isinstance(final_report, dict) else None
