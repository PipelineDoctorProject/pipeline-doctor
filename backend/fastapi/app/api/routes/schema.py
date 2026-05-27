from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schema_change_event import SchemaChangeEvent
from app.dependencies.auth import require_tenant_user
from app.services.access_control import require_accessible_model


router = APIRouter(prefix="/schema", tags=["Schema Evolution"])


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



from fastapi import HTTPException
from app.models.baseline import Baseline
from app.services.quality.baseline_service import create_baseline_version


@router.post("/approve/{event_id}")
def approve_schema_change(event_id: int, db: Session = Depends(get_db), current_user=Depends(require_tenant_user)):

    event = db.get(SchemaChangeEvent, event_id)

    if not event:
        raise HTTPException(404, "Schema change event not found")

    if event.status != "pending":
        raise HTTPException(400, "Already processed")

    # get current baseline
    baseline = db.get(Baseline, event.baseline_id)

    if not baseline:
        raise HTTPException(404, "Baseline not found")

    #  merge schema
    updated_schema = baseline.schema.copy()
    updated_profile = baseline.profile.copy()

    for col in event.new_columns:
        updated_schema[col] = "object"  # temp assumption
        updated_profile[col] = {
            "type": "categorical",
            "unique_values": []
        }

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
    db.commit()
    

    return {
        "message": "Schema approved",
        "new_baseline_version": new_baseline.version
    }
