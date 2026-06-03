from fastapi import APIRouter, Depends, Response, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.auth import (
    SignupRequest,
    VerifyOTPRequest,
    ResendOTPRequest,
    LoginRequest
)

from app.services.auth.auth_service import (
    signup_user,
    verify_otp,
    resend_otp,
    login_user,
    refresh_access_token,
    logout_user
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


def _cookie_settings(request: Request) -> dict:
    forwarded_proto = request.headers.get("x-forwarded-proto")
    scheme = (forwarded_proto or request.url.scheme or "").lower()
    secure = scheme == "https"

    return {
        "httponly": True,
        "secure": secure,
        "samesite": "none" if secure else "lax",
        "path": "/",
    }


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
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    result = verify_otp(
        db=db,
        email=data.email,
        otp=data.otp
    )

    cookie_options = _cookie_settings(request)

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        max_age=60 * 30,
        **cookie_options,
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        max_age=60 * 60 * 24 * 7,
        **cookie_options,
    )

    return {
        "message": "OTP verified",
        "onboarding_required": result["onboarding_required"],
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": "bearer",
    }


@router.post("/resend-otp")
def resend_otp_route(
    data: ResendOTPRequest,
    db: Session = Depends(get_db)
):
    return resend_otp(
        db=db,
        email=data.email
    )


# ======================================
# LOGIN
# ======================================
@router.post("/login")
def login_route(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    result = login_user(
        db=db,
        email=data.email,
        password=data.password
    )

    cookie_options = _cookie_settings(request)

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        max_age=60 * 30,
        **cookie_options,
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        max_age=60 * 60 * 24 * 7,
        **cookie_options,
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
        **_cookie_settings(request),
    )

    return {
        "message": "Token refreshed",
        "access_token": result["access_token"],
        "token_type": result["token_type"],
    }

# ======================================
# LOGOUT
# ======================================
@router.post("/logout")
def logout_route(
    response: Response
):

    return logout_user(response)
