# app/routes/dashboard.py

from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    Depends
)

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun
from app.models.incident import Incident
from app.services.slack_service import get_workspace_for_tenant

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/me")
def get_dashboard_context(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user = current_user

    tenant = None

    if user.tenant_id:

        tenant = (
            db.query(Tenant)
            .filter(Tenant.id == user.tenant_id)
            .first()
        )

    return {

        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        },

        "workspace": {
            "tenant_id": tenant.id if tenant else None,
            "workspace_name": tenant.name if tenant else None,
            "schema_name": (
                tenant.schema_name
                if tenant else None
            ),
            "slack_connected": bool(get_workspace_for_tenant(db, tenant.id)) if tenant else False,
        },

        "stats": {
            "total_models": db.query(func.count(MLModel.id)).scalar() if user.tenant_id else 0,
            "total_runs": db.query(func.count(PipelineRun.id)).scalar() if user.tenant_id else 0,
            "open_incidents": (
                db.query(func.count(Incident.id))
                .filter(Incident.status == "open")
                .scalar()
                if user.tenant_id else 0
            ),
        },

        "is_onboarded": bool(user.tenant_id)
    }
