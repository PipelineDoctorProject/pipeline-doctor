from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.auth import require_tenant_user
from app.db.session import get_db

from app.models.incident import Incident
from app.models.agent_run import AgentRun
from app.models.agent_step_log import AgentStepLog

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

    return incident


@router.get("/", response_model=list[IncidentResponse])
def list_incidents(
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):

    incidents = (
        db.query(Incident)
        .order_by(Incident.id.desc())
        .all()
    )

    return incidents


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