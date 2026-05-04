from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_quality import DataQualityFinding

router = APIRouter(prefix="/data-quality-findings", tags=["Data Quality Findings"])


@router.get("/")
def list_data_quality_findings(db: Session = Depends(get_db)):
    return db.query(DataQualityFinding).order_by(DataQualityFinding.id.desc()).all()