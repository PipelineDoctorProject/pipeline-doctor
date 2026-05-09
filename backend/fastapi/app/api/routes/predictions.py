from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.prediction_log import PredictionLog

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/")
def list_predictions(db: Session = Depends(get_db)):
    return db.query(PredictionLog).order_by(PredictionLog.id.desc()).limit(100).all()