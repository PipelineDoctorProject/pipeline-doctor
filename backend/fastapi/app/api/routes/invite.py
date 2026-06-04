from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    Response
)

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.invite import (
    InviteMemberRequest,
    AcceptInviteRequest
)

from app.services.auth.invite_service import (
    invite_member
)

from app.services.auth.accept_invite_service import (
    accept_invite
)
from app.api.routes.auth import _cookie_settings

router = APIRouter(
    prefix="/invite",
    tags=["Invite"]
)


# ==========================================
# INVITE MEMBER
# ==========================================
@router.post("/member")
def invite_member_route(
    data: InviteMemberRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can invite users"
        )

    return invite_member(
        db=db,
        admin_user=user,
        email=data.email
    )


# ==========================================
# ACCEPT INVITE
# ==========================================
@router.post("/accept")
def accept_invite_route(
    data: AcceptInviteRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    result = accept_invite(
        db=db,
        token=data.token,
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
        "message": "Invitation accepted",
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
    }