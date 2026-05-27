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
from app.api.routes.auth import _cookie_settings

router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"]
)


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
        "message": result["message"],
        "tenant_id": result["tenant_id"],
        "workspace_name": result["workspace_name"],
        "schema_name": result["schema_name"],
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": "bearer",
    }
