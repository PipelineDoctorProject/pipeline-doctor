from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.auth.delete_tenant_service import (
    delete_tenant
)

router = APIRouter(
    prefix="/tenant",
    tags=["Tenant"]
)


@router.delete("/{tenant_id}")
def delete_tenant_route(
    tenant_id: str,
    db: Session = Depends(get_db)
):

    return delete_tenant(
        db=db,
        tenant_id=tenant_id
    )