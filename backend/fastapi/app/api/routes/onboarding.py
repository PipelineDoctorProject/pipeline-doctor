from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    Response
)

from fastapi.security import HTTPBearer

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.onboarding import (
    CompanyOnboardingRequest
)

from app.services.auth.onboarding_service import (
    create_company
)

router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"]
)

security = HTTPBearer()


@router.post(
    "/company",
    dependencies=[Depends(security)]
)
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

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=False,
        samesite="Lax"
    )

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=False,
        samesite="Lax"
    )

    return {
        "message": result["message"],
        "tenant_id": result["tenant_id"],
        "schema_name": result["schema_name"]
    }