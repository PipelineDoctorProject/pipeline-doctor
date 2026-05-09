from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.jwt import decode_token

from app.db.session import SessionLocal
from app.utils.schema_utils import set_schema


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # Default values
        request.state.user = None
        request.state.schema = None
        request.state.db = None

        auth_header = request.headers.get("Authorization")

        print("AUTH HEADER:", auth_header)

        # Validate Authorization header
        if auth_header:

            try:

                # Extract token
                token = auth_header.replace("Bearer ", "")

                # Decode JWT
                payload = decode_token(token)

                print("TOKEN PAYLOAD:", payload)

                # Save user payload
                request.state.user = payload

                # Get schema name
                schema_name = payload.get("schema_name")

                # If tenant schema exists
                if schema_name:

                    request.state.schema = schema_name

                    db = SessionLocal()

                    # Switch PostgreSQL schema
                    set_schema(db, schema_name)

                    request.state.db = db

                    print("SCHEMA SET:", schema_name)

            except Exception as e:

                print("AUTH ERROR:", str(e))

        else:
            print("NO AUTH HEADER")

        # Continue request
        response = await call_next(request)

        # Close DB connection
        db = request.state.db

        if db:
            db.close()

        return response