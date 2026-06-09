from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token, decode_token, create_refresh_token
from app.utils.otp_utils import generate_otp
from app.tasks.email_tasks import send_otp_email_task
from app.config.settings import get_auth_cookie_settings


AUTH_COOKIE_SETTINGS = get_auth_cookie_settings()


def signup_user(db: Session, email: str, password: str):
    normalized_email = email.strip().lower()

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user and existing_user.is_verified:
        raise HTTPException(400, "User already exists")

    otp = generate_otp()

    if existing_user:
        existing_user.hashed_password = hash_password(password)
        existing_user.otp_code = otp
        db.commit()
        send_otp_email_task.delay(normalized_email, otp)
        return {"message": "OTP sent"}

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
    normalized_otp = "".join(str(otp).split())

    user = db.query(User).filter(User.email == normalized_email).first()

    if not user:
        raise HTTPException(404, "No pending signup found for this email")

    if user.is_verified:
        raise HTTPException(400, "Account already verified. Please login.")

    if not user.otp_code or user.otp_code != normalized_otp:
        raise HTTPException(400, "Invalid OTP. Use the latest code from your email.")

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


def resend_otp(db: Session, email: str):
    normalized_email = email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()

    if not user:
        raise HTTPException(404, "No pending signup found for this email")

    if user.is_verified:
        raise HTTPException(400, "Account already verified. Please login.")

    otp = generate_otp()
    user.otp_code = otp
    db.commit()

    send_otp_email_task.delay(normalized_email, otp)

    return {"message": "OTP sent"}


def login_user(db: Session, email: str, password: str):
    normalized_email = email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ACCOUNT_NOT_FOUND",
                "message": "No OpsSight account exists for this email. Please create an account first.",
            },
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Please verify your email with the OTP before logging in.",
            },
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PASSWORD_NOT_SET",
                "message": "Your invite is pending password setup. Please use the invitation link from your email.",
            },
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_PASSWORD",
                "message": "The password you entered is incorrect. Please try again.",
            },
        )

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
        path="/",
        secure=AUTH_COOKIE_SETTINGS["secure"],
        samesite=AUTH_COOKIE_SETTINGS["samesite"],
    )

    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=AUTH_COOKIE_SETTINGS["secure"],
        samesite=AUTH_COOKIE_SETTINGS["samesite"],
    )

    return {
        "message": "Logged out successfully"
    }
