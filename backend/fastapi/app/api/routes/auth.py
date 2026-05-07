from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.auth import (
    SignupRequest,
    VerifyOTPRequest,
    LoginRequest,
    RefreshTokenRequest
)

from app.services.auth.auth_service import (
    signup_user,
    verify_otp,
    login_user,
    refresh_access_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# ======================================
# SIGNUP
# ======================================
@router.post("/signup")
def signup_route(
    data: SignupRequest,
    db: Session = Depends(get_db)
):

    return signup_user(
        db=db,
        email=data.email,
        password=data.password
    )


# ======================================
# VERIFY OTP
# ======================================
@router.post("/verify-otp")
def verify_otp_route(
    data: VerifyOTPRequest,
    db: Session = Depends(get_db)
):

    return verify_otp(
        db=db,
        email=data.email,
        otp=data.otp
    )


# ======================================
# LOGIN
# ======================================
@router.post("/login")
def login_route(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    return login_user(
        db=db,
        email=data.email,
        password=data.password
    )


# ======================================
# REFRESH TOKEN
# ======================================
@router.post("/refresh")
def refresh_token_route(
    data: RefreshTokenRequest
):

    return refresh_access_token(
        data.refresh_token
    )