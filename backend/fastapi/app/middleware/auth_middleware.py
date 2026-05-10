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

        auth_header = request.headers.get("Authorization")

        if auth_header:

            try:
                token = auth_header.replace("Bearer ", "")
                payload = decode_token(token)

                db = SessionLocal()

                user = (
                    db.query(User)
                    .filter(User.id == payload["user_id"])
                    .first()
                )

                if user:
                    request.state.user = user  # ✅ ORM OBJECT

                    if user.tenant_id:
                        request.state.schema = user.tenant_id
                        set_schema(db, user.tenant_id)
                        request.state.db = db

            except Exception as e:
                print("AUTH ERROR:", e)

        response = await call_next(request)

        if request.state.db:
            request.state.db.close()

        return response