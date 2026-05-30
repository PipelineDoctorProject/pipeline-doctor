from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User

from app.core.security import hash_password

from app.core.jwt import (
    create_access_token,
    create_refresh_token
)


def accept_invite(
    db: Session,
    token: str,
    password: str
):

    user = (
        db.query(User)
        .filter(User.invite_token == token)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Invalid invite"
        )

    user.hashed_password = hash_password(password)

    user.is_verified = True
    user.invite_accepted = True
    user.invite_token = None
    user.otp_code = None

    db.commit()

    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id
    })

    refresh_token = create_refresh_token({
        "user_id": user.id
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
