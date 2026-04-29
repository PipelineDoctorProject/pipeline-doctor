from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentResponse

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("/", response_model=IncidentResponse)
def create_incident(data: IncidentCreate, db: Session = Depends(get_db)):
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
def list_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).order_by(Incident.id.desc()).all()