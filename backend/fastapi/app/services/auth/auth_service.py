from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token, decode_token, create_refresh_token
from app.utils.otp_utils import generate_otp
from app.tasks.email_tasks import send_otp_email_task


def signup_user(db: Session, email: str, password: str):
    normalized_email = email.strip().lower()

    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(400, "User already exists")

    otp = generate_otp()

    user = User(
        email=normalized_email,
        hashed_password=hash_password(password),
        otp_code=otp,
        is_verified=False,
        role="admin"
    )

    db.add(user)
    db.commit()

    send_otp_email_task.delay(normalized_email, otp)

    return {"message": "OTP sent"}


def verify_otp(db: Session, email: str, otp: str):
    normalized_email = email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or user.otp_code != otp:
        raise HTTPException(400, "Invalid OTP")

    user.is_verified = True
    user.otp_code = None
    db.commit()

    access_token = create_access_token({
        "user_id": user.id   # ONLY ID
    })

    refresh_token = create_refresh_token({
        "user_id": user.id
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "onboarding_required": True
    }


def login_user(db: Session, email: str, password: str):
    normalized_email = email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")

    access_token = create_access_token({
        "user_id": user.id
    })

    refresh_token = create_refresh_token({
        "user_id": user.id
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

from app.core.jwt import create_access_token, decode_token
from fastapi import HTTPException


def refresh_access_token(
    db,
    refresh_token: str
):

    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    user = (
        db.query(User)
        .filter(User.id == payload["user_id"])
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    new_access_token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id
    })

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

def logout_user(response):

    response.delete_cookie(
        key="access_token",
        path="/"
    )

    response.delete_cookie(
        key="refresh_token",
        path="/"
    )

    return {
        "message": "Logged out successfully"
    }
