from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User

from app.core.security import (
    hash_password,
    verify_password
)

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token
)

from app.utils.otp_utils import generate_otp
from app.utils.email_utils import send_otp_email


# ==========================================
# SIGNUP
# ==========================================
def signup_user(
    db: Session,
    email: str,
    password: str
):

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    otp = generate_otp()

    user = User(
        email=email,
        hashed_password=hash_password(password),
        otp_code=otp,
        is_verified=False,
        role="admin"
    )

    db.add(user)
    db.commit()

    send_otp_email(email, otp)

    return {
        "message": "OTP sent successfully"
    }


# ==========================================
# VERIFY OTP + AUTO LOGIN
# ==========================================
def verify_otp(
    db: Session,
    email: str,
    otp: str
):

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.otp_code != otp:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    user.is_verified = True
    user.otp_code = None

    db.commit()

    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "schema_name": None,
        "role": user.role
    })

    refresh_token = create_refresh_token({
        "user_id": user.id
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "onboarding_required": True
    }

# ==========================================
# LOGIN
# ==========================================
def login_user(
    db: Session,
    email: str,
    password: str
):

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=401,
            detail="Email not verified"
        )

    if not verify_password(
        password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email
    })

    refresh_token = create_refresh_token({
        "user_id": user.id
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# ==========================================
# REFRESH ACCESS TOKEN
# ==========================================
def refresh_access_token(
    refresh_token: str
):

    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":

        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    new_access_token = create_access_token({
        "user_id": payload["user_id"]
    })

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }