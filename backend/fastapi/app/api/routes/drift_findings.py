from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies.auth import require_tenant_user
from app.db.session import get_db
from app.models.drift_finding import DriftFinding

from app.schemas.drift import DriftResponse

router = APIRouter(prefix="/drift-findings", tags=["Drift Findings"])


@router.get("/", response_model=list[DriftResponse])
def list_drift_findings(db: Session = Depends(get_db),current_user=Depends(require_tenant_user)):
    return db.query(DriftFinding).order_by(DriftFinding.id.desc()).all()