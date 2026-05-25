from fastapi import APIRouter, Depends, Response, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.auth import (
    SignupRequest,
    VerifyOTPRequest,
    LoginRequest
)

from app.services.auth.auth_service import (
    signup_user,
    verify_otp,
    login_user,
    refresh_access_token,
    logout_user
)
from app.config.settings import get_auth_cookie_settings

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


AUTH_COOKIE_SETTINGS = get_auth_cookie_settings()


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
        max_age=60 * 30,
        **AUTH_COOKIE_SETTINGS,
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        max_age=60 * 60 * 24 * 7,
        **AUTH_COOKIE_SETTINGS,
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
        max_age=60 * 30,
        **AUTH_COOKIE_SETTINGS,
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        max_age=60 * 60 * 24 * 7,
        **AUTH_COOKIE_SETTINGS,
    )

    return {
        "message": "Login successful",
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": "bearer",
    }


# ======================================
# REFRESH TOKEN
# ======================================
@router.post("/refresh")
def refresh_token_route(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing"
        )

    result = refresh_access_token(
    db=db,
    refresh_token=refresh_token
)

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        max_age=60 * 30,
        **AUTH_COOKIE_SETTINGS,
    )

    return {
        "message": "Token refreshed"
    }

# ======================================
# LOGOUT
# ======================================
@router.post("/logout")
def logout_route(
    response: Response
):

    return logout_user(response)
