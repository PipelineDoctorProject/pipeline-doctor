from fastapi import APIRouter, Depends, HTTPException, Query
import json

from sqlalchemy.orm import Session

from app.dependencies.auth import require_tenant_user
from app.db.session import get_db

from app.models.incident import Incident
from app.models.agent_run import AgentRun
from app.models.agent_step_log import AgentStepLog
from app.models.drift_finding import DriftFinding
from app.models.pipeline_run import PipelineRun
from app.services.incidents.live_events import publish_incident_event

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

    db.commit()

    db.refresh(incident)
    publish_incident_event("incident_created", incident)

    return incident


@router.get("/", response_model=list[IncidentResponse])
def list_incidents(
    model_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):

    return _serialized_incidents(
        db,
        model_id=model_id,
    )


@router.get("/filtered")
def filter_incidents(
    model_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):

    return _serialized_incidents(
        db,
        model_id=model_id,
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

    return incident


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

    runs = (
        db.query(AgentRun)
        .filter(
            AgentRun.pipeline_run_id == incident.run_id
        )
        .order_by(AgentRun.id.desc())
        .all()
    )

    return runs


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
        "severity": incident.severity,
        "status": incident.status,
        "created_at": incident.created_at,
        "guidance": _build_guidance(
            incident,
            drift_finding,
            rca_report
        ),
        "rca_report": rca_report,
    }


def _serialized_incidents(
    db: Session,
    model_id: int | None = None,
):

    query = db.query(Incident)

    if model_id is not None:
        query = (
            query
            .join(PipelineRun, Incident.run_id == PipelineRun.id)
            .filter(PipelineRun.model_id == model_id)
        )

    incidents = query.order_by(Incident.id.desc()).all()

    drift_ids = [
        incident.finding_id
        for incident in incidents
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
        for incident in incidents
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
