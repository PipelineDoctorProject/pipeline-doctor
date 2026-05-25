from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    Response
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.onboarding import (
    CompanyOnboardingRequest
)

from app.services.auth.onboarding_service import (
    create_company
)
from app.config.settings import get_auth_cookie_settings

router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"]
)


AUTH_COOKIE_SETTINGS = get_auth_cookie_settings()


@router.post("/company")
def create_company_route(
    data: CompanyOnboardingRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    result = create_company(
        db=db,
        user_id=user.id,
        company_name=data.company_name
    )

    # Update cookies with tenant-aware tokens
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        max_age=60 * 30,
        **AUTH_COOKIE_SETTINGS,
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        max_age=60 * 60 * 24 * 7,
        **AUTH_COOKIE_SETTINGS,
    )

    return {
        "message": result["message"],
        "tenant_id": result["tenant_id"],
        "schema_name": result["schema_name"]
    }
