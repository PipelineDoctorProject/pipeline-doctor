# app/routes/dashboard.py

from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    Depends
)

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tenant import Tenant

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/me")
def get_dashboard_context(
    request: Request,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

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
            )
        },

        "is_onboarded": bool(user.tenant_id)
    }