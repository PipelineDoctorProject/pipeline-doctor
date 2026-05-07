from sqlalchemy.orm import Session
from app.models.baseline import Baseline


def get_active_baseline(db: Session, model_id: int):
    baseline = (
        db.query(Baseline)
        .filter(
            Baseline.model_id == model_id,
            Baseline.is_active == True,
            Baseline.status == "approved"
        )
        .first()
    )

    if not baseline:
        raise Exception("No active baseline found")

    return baseline