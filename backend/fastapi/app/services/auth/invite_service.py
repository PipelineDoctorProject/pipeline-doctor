import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.utils.email_utils import send_invite_email


def invite_member(db: Session, admin_user, email: str):

    if admin_user.role != "admin":
        raise HTTPException(403, "Only admin can invite users")

    if not admin_user.tenant_id:
        raise HTTPException(400, "User not onboarded")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "User already exists")

    token = str(uuid.uuid4())

    user = User(
        email=email,
        role="member",
        tenant_id=admin_user.tenant_id,
        invite_token=token,
        is_verified=True,
        invite_accepted=False
    )

    db.add(user)
    db.commit()

    send_invite_email(email, f"http://localhost:8000/invite/accept?token={token}")

    return {"message": "Invitation sent","invite_token": token}