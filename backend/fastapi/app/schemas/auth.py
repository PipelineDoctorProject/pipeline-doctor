from pydantic import BaseModel


# =========================
# SIGNUP
# =========================
class SignupRequest(BaseModel):
    email: str
    password: str


# =========================
# VERIFY OTP
# =========================
class VerifyOTPRequest(BaseModel):
    email: str
    otp: str


# =========================
# LOGIN
# =========================
class LoginRequest(BaseModel):
    email: str
    password: str


# =========================
# REFRESH TOKEN
# =========================
class RefreshTokenRequest(BaseModel):
    refresh_token: str