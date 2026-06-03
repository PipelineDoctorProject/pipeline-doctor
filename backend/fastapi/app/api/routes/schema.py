from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schema_change_event import SchemaChangeEvent
from app.dependencies.auth import require_tenant_user
from app.services.access_control import require_accessible_model


router = APIRouter(prefix="/schema", tags=["Schema Evolution"])


class SchemaApprovalRequest(BaseModel):
    approved_feature_columns: list[str] = Field(default_factory=list)
    feature_decisions: dict[str, str] = Field(default_factory=dict)


@router.get("/pending/{model_id}")
def get_pending_events(model_id: int, db: Session = Depends(get_db), current_user=Depends(require_tenant_user)):
    require_accessible_model(db, model_id, current_user.tenant_id)

    events = (
        db.query(SchemaChangeEvent)
        .filter(
            SchemaChangeEvent.model_id == model_id,
            SchemaChangeEvent.status == "pending"
        )
        .all()
    )

    return events


@router.post("/reject/{event_id}")
def reject_schema_change(event_id: int, db: Session = Depends(get_db), current_user=Depends(require_tenant_user)):
    event = db.get(SchemaChangeEvent, event_id)

    if not event:
        raise HTTPException(404, "Schema change event not found")

    require_accessible_model(db, event.model_id, current_user.tenant_id)

    if event.status != "pending":
        raise HTTPException(400, "Already processed")

    event.status = "rejected"
    event.feature_decisions = {
        "decision": "rejected",
        "rejected_by": current_user.email,
        "reason": "Schema change rejected by workspace admin.",
    }
    db.commit()

    return {"message": "Schema change rejected"}

from app.models.baseline import Baseline
from app.services.quality.baseline_service import create_baseline_version


@router.post("/approve/{event_id}")
def approve_schema_change(
    event_id: int,
    request: SchemaApprovalRequest | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):

    event = db.get(SchemaChangeEvent, event_id)

    if not event:
        raise HTTPException(404, "Schema change event not found")

    if event.status != "pending":
        raise HTTPException(400, "Already processed")

    require_accessible_model(db, event.model_id, current_user.tenant_id)

    # get current baseline
    baseline = db.get(Baseline, event.baseline_id)

    if not baseline:
        raise HTTPException(404, "Baseline not found")

    #  merge schema
    updated_schema = baseline.schema.copy()
    updated_profile = baseline.profile.copy()

    from app.models.ml_model import MLModel
    from app.services.quality.schema_evolution import (
        normalize_approved_feature_columns,
        profile_from_feature_candidate,
    )

    request = request or SchemaApprovalRequest()
    candidates = event.feature_candidates or []
    candidate_by_name = {str(item.get("column")): item for item in candidates}

    for col in event.new_columns or []:
        candidate = candidate_by_name.get(str(col), {})
        updated_schema[col] = candidate.get("dtype") or "object"
        updated_profile[col] = profile_from_feature_candidate(
            {"column": col, **candidate}
        )

    approved_feature_columns = normalize_approved_feature_columns(
        request.approved_feature_columns,
        candidates,
    )
    rejected_requested_columns = sorted(
        set(request.approved_feature_columns or []) - set(approved_feature_columns)
    )

    # create new baseline
    new_baseline = create_baseline_version(
    db,
    model_id=event.model_id,
    schema=updated_schema,
    profile=updated_profile,
    approved=True
    )

    # IMPORTANT: activate it
    from app.services.quality.baseline_service import activate_baseline
    activate_baseline(db, new_baseline.id)

    # update event
    event.status = "approved"
    event.feature_decisions = {
        "approved_by": current_user.email,
        "approved_feature_columns": approved_feature_columns,
        "rejected_requested_columns": rejected_requested_columns,
        "feature_decisions": request.feature_decisions,
        "baseline_version": new_baseline.version,
    }

    if approved_feature_columns:
        model = db.get(MLModel, event.model_id)
        if model:
            existing_features = [
                str(feature)
                for feature in (model.expected_features or [])
                if str(feature).strip()
            ]
            for feature in approved_feature_columns:
                if feature not in existing_features:
                    existing_features.append(feature)
            model.expected_features = existing_features

    db.commit()
    

    return {
        "message": "Schema approved",
        "new_baseline_version": new_baseline.version,
        "approved_feature_columns": approved_feature_columns,
        "rejected_requested_columns": rejected_requested_columns,
    }
