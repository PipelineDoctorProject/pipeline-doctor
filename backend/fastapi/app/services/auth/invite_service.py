import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.config.settings import FRONTEND_URL
from app.models.user import User
from app.tasks.email_tasks import send_invite_email_task


def invite_member(db: Session, admin_user, email: str):
    normalized_email = email.strip().lower()

    if admin_user.role != "admin":
        raise HTTPException(403, "Only admin can invite users")

    if not admin_user.tenant_id:
        raise HTTPException(400, "User not onboarded")

    existing_user = db.query(User).filter(User.email == normalized_email).first()

    if existing_user and existing_user.invite_accepted:
        raise HTTPException(400, "User already exists")

    if (
        existing_user
        and existing_user.tenant_id
        and existing_user.tenant_id != admin_user.tenant_id
    ):
        raise HTTPException(409, "User already belongs to another workspace")

    token = str(uuid.uuid4())

    if existing_user:
        user = existing_user
        user.role = "member"
        user.tenant_id = admin_user.tenant_id
        user.invite_token = token
        user.is_verified = True
        user.invite_accepted = False
        message = "Invitation resent"
    else:
        user = User(
            email=normalized_email,
            role="member",
            tenant_id=admin_user.tenant_id,
            invite_token=token,
            is_verified=True,
            invite_accepted=False
        )
        db.add(user)
        message = "Invitation sent"

    db.commit()

    invite_link = f"{FRONTEND_URL.rstrip('/')}/accept-invite?token={token}"
    send_invite_email_task.delay(normalized_email, invite_link)

    return {
        "message": message,
        "invite_token": token,
        "email": normalized_email,
    }
