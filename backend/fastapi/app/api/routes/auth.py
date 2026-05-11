from fastapi import APIRouter, Depends, Response
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
    response: Response,
    db: Session = Depends(get_db)
):

    result = verify_otp(
        db=db,
        email=data.email,
        otp=data.otp
    )

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=False,
        samesite="Lax"
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=False,
        samesite="Lax"
    )

    return {
        "message": "OTP verified",
        "onboarding_required": result["onboarding_required"]
    }


# ======================================
# LOGIN
# ======================================
@router.post("/login")
def login_route(
    data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):

    result = login_user(
        db=db,
        email=data.email,
        password=data.password
    )

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=False,
        samesite="Lax"
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=False,
        samesite="Lax"
    )

    return {
        "message": "Login successful"
    }


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