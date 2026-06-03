from fastapi import APIRouter, Depends, HTTPException
import json

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_tenant_user
from app.models.incident import Incident
from app.models.incident_report import IncidentReport
from app.schemas.report import IncidentReportResponse, IncidentReportSummary
from app.services.access_control import require_accessible_model
from app.services.incidents.report_service import create_incident_report_version


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/incidents/{incident_id}", response_model=list[IncidentReportSummary])
def list_incident_report_versions(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    incident = _get_authorized_incident(db, incident_id, current_user.tenant_id)
    return (
        db.query(IncidentReport)
        .filter(IncidentReport.incident_id == incident.id)
        .order_by(IncidentReport.version.desc())
        .all()
    )


@router.get("/incidents/{incident_id}/latest", response_model=IncidentReportResponse)
def get_latest_incident_report(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    incident = _get_authorized_incident(db, incident_id, current_user.tenant_id)
    report = (
        db.query(IncidentReport)
        .filter(IncidentReport.incident_id == incident.id)
        .order_by(IncidentReport.version.desc())
        .first()
    )
    if not report:
        report = _backfill_report_from_incident_description(db, incident)
    if not report:
        raise HTTPException(status_code=404, detail="No report has been generated for this incident yet.")
    return report


@router.get("/{report_id}", response_model=IncidentReportResponse)
def get_incident_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    report = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    _get_authorized_incident(db, report.incident_id, current_user.tenant_id)
    return report


def _get_authorized_incident(db: Session, incident_id: int, tenant_id: str) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    if not incident.run:
        raise HTTPException(status_code=404, detail="Incident run not found.")

    require_accessible_model(db, incident.run.model_id, tenant_id)
    return incident


def _backfill_report_from_incident_description(
    db: Session,
    incident: Incident,
) -> IncidentReport | None:
    try:
        payload = json.loads(incident.description or "{}")
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict) or "final_report" not in payload:
        return None

    report = create_incident_report_version(
        db,
        incident=incident,
        rca_payload=payload,
        generator="deterministic_backfill",
        generator_model=payload.get("model"),
    )
    db.commit()
    db.refresh(report)
    return report
