import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.models.tenant import Tenant

from app.utils.schema_utils import create_schema

from app.core.jwt import (
    create_access_token,
    create_refresh_token
)


def create_company(
    db: Session,
    user_id: str,
    company_name: str
):

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        if user.tenant_id:
            raise HTTPException(
                status_code=400,
                detail="Company already created"
            )

        schema_name = (
            f"tenant_"
            f"{company_name.lower().replace(' ', '_')}_"
            f"{uuid.uuid4().hex[:6]}"
        )

        tenant = Tenant(
            name=company_name,
            schema_name=schema_name
        )

        db.add(tenant)

        db.flush()

        # CREATE SCHEMA
        create_schema(db, schema_name)

        # LINK USER
        user.tenant_id = tenant.id

        db.commit()

        db.refresh(tenant)

        access_token = create_access_token({
            "user_id": user.id,
            "tenant_id": tenant.id,
            "schema_name": tenant.schema_name,
            "role": user.role
        })

        refresh_token = create_refresh_token({
            "user_id": user.id,
            "tenant_id": tenant.id,
            "schema_name": tenant.schema_name,
            "role": user.role
        })

        return {
            "message": "Company created",
            "tenant_id": tenant.id,
            "schema_name": schema_name,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )