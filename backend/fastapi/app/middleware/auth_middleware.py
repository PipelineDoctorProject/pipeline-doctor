from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.jwt import decode_token
from app.db.session import SessionLocal
from app.models.user import User
from app.utils.schema_utils import set_schema


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        request.state.user = None
        request.state.db = None
        request.state.schema = None

        db = SessionLocal()

        try:

            # Skip refresh route
            if request.url.path == "/auth/refresh":

                request.state.db = db

                response = await call_next(request)

                return response

            token = request.cookies.get("access_token")

            # Swagger bearer support
            if not token:

                auth_header = request.headers.get("Authorization")

                if (
                    auth_header and
                    auth_header.startswith("Bearer ")
                ):

                    token = auth_header.split(" ")[1]

            if token:

                payload = decode_token(token)

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

            request.state.db = db

            response = await call_next(request)

            return response

        except Exception as e:

            print("AUTH ERROR:", e)

            request.state.user = None
            request.state.schema = None
            request.state.db = db

            response = await call_next(request)

            return response

        finally:

            db.close()