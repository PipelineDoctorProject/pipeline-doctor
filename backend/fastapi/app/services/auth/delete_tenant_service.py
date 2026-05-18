from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import text

from app.models.tenant import Tenant


def delete_tenant(
    db: Session,
    tenant_id: str
):

    tenant = (
        db.query(Tenant)
        .filter(Tenant.id == tenant_id)
        .first()
    )

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )

    try:

        # DROP SCHEMA
        db.execute(
            text(
                f'DROP SCHEMA IF EXISTS "{tenant.schema_name}" CASCADE'
            )
        )

        # DELETE TENANT
        db.delete(tenant)

        db.commit()

        return {
            "message": "Tenant deleted successfully"
        }

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )