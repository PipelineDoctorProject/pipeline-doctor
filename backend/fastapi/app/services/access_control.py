from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ml_model import MLModel


def require_accessible_model(
    db: Session,
    model_id: int,
    tenant_id: str | None = None,
) -> MLModel:
    model = (
        db.query(MLModel)
        .filter(MLModel.id == model_id)
        .first()
    )

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if tenant_id and model.tenant_id != tenant_id:
        # Do not leak whether the model exists in another tenant.
        raise HTTPException(status_code=404, detail="Model not found")

    return model

