from fastapi import Request, HTTPException


def get_current_user(request: Request):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    return user


def require_tenant_user(request: Request):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    if not user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Workspace required"
        )

    return user