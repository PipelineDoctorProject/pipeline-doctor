from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies.auth import require_tenant_user

from app.db.session import get_db
from app.models.prediction_log import PredictionLog

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/")
def list_predictions(db: Session = Depends(get_db),current_user=Depends(require_tenant_user)):
    return db.query(PredictionLog).order_by(PredictionLog.id.desc()).limit(100).all()