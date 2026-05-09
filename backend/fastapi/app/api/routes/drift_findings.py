from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.drift_finding import DriftFinding

router = APIRouter(prefix="/drift-findings", tags=["Drift Findings"])


@router.get("/")
def list_drift_findings(db: Session = Depends(get_db)):
    return db.query(DriftFinding).order_by(DriftFinding.id.desc()).all()