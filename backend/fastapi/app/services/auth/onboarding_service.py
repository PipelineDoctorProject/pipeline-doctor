import uuid

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.models.tenant import Tenant

from app.core.jwt import (
    create_access_token,
    create_refresh_token
)

from app.utils.schema_utils import create_schema


def create_company(
    db: Session,
    user_id: str,
    company_name: str
):

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

    clean_name = (
        company_name
        .lower()
        .replace(" ", "_")
    )

    schema_name = (
        f"tenant_{clean_name}_{uuid.uuid4().hex[:6]}"
    )

    tenant = Tenant(
        name=company_name,
        schema_name=schema_name
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    create_schema(db, schema_name)

    user.tenant_id = tenant.id

    db.commit()

    # NEW TOKENS WITH SCHEMA

    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "schema_name": schema_name
    })

    refresh_token = create_refresh_token({
        "user_id": user.id
    })

    return {
        "message": "Company created",
        "access_token": access_token,
        "refresh_token": refresh_token
    }