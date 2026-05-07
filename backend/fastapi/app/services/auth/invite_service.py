import uuid

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User

from app.utils.email_utils import send_invite_email


def invite_member(
    db: Session,
    admin_user,
    email: str
):

    # Only admin can invite
    if admin_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can invite users"
        )

    existing = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    invite_token = str(uuid.uuid4())

    user = User(
        email=email,
        role="member",
        tenant_id=admin_user["tenant_id"],
        is_verified=True,
        invite_token=invite_token,
        invite_accepted=False
    )

    db.add(user)
    db.commit()

    invite_link = (
        f"http://localhost:3000/accept-invite/"
        f"{invite_token}"
    )

    send_invite_email(
        email=email,
        invite_link=invite_link
    )

    return {
        "message": "Invitation sent"
    }