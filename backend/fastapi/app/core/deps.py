from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from app.core.jwt import decode_token

security = HTTPBearer()

def get_current_user(token=Depends(security)):
    try:
        payload = decode_token(token.credentials)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_schema_name(user=Depends(get_current_user)):
    return user["schema_name"]