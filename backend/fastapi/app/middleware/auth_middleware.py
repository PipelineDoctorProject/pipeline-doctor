from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.jwt import decode_token

from app.db.session import SessionLocal
from app.utils.schema_utils import set_schema


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        request.state.user = None
        request.state.schema = None
        request.state.db = None

        auth_header = request.headers.get("Authorization")

        # Validate Bearer token
        if auth_header and auth_header.startswith("Bearer "):

            try:

                token = auth_header.split(" ")[1]

                payload = decode_token(token)

                request.state.user = payload

                schema_name = payload.get("schema_name")

                if schema_name:

                    request.state.schema = schema_name

                    db = SessionLocal()

                    set_schema(db, schema_name)

                    request.state.db = db

            except Exception as e:

                print("AUTH ERROR:", e)

        response = await call_next(request)

        db = request.state.db

        if db:
            db.close()

        return response