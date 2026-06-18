from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.jwt import decode_token
from app.db.session import SessionLocal
from app.models.user import User
from app.utils.schema_utils import set_schema


class AuthMiddleware(BaseHTTPMiddleware):
    PUBLIC_PATHS = {
        "/auth/login",
        "/auth/signup",
        "/auth/verify-otp",
        "/auth/refresh",
        "/auth/logout",
    }

    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        request.state.db = None
        request.state.schema = None

        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        token = None

        # Prefer the explicit bearer token used by the SPA.
        # Falling back to cookies is still useful for refresh-based
        # sessions, but the cookie must not override a newer header.
        if (
            auth_header and
            auth_header.startswith("Bearer ")
        ):
            token = auth_header.split(" ", 1)[1]
        else:
            token = request.cookies.get("access_token")

        if not token:
            return await call_next(request)

        try:
            payload = decode_token(token)
        except Exception as exc:
            print("AUTH ERROR:", exc)
            return await call_next(request)

        db = SessionLocal()

        try:

            user = (
                db.query(User)
                .filter(User.id == payload["user_id"])
                .first()
            )

            if user:
                request.state.user = user

                from app.models.tenant import Tenant

                tenant = (
                    db.query(Tenant)
                    .filter(Tenant.id == user.tenant_id)
                    .first()
                )

                if tenant and tenant.schema_name:
                    request.state.schema = tenant.schema_name
                    set_schema(db, tenant.schema_name)

        finally:
            db.close()

        return await call_next(request)
