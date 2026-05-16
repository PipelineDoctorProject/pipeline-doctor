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
    response: Response,
    db: Session = Depends(get_db)
):

    result = accept_invite(
        db=db,
        token=data.token,
        password=data.password
    )

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=True,
        samesite="None",
        path="/",
        max_age=60 * 30
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="None",
        path="/",
        max_age=60 * 60 * 24 * 7
    )

    return {
        "message": "Invitation accepted"
    }