from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
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
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    return create_company(
        db=db,
        user_id=user["user_id"],
        company_name=data.company_name
    )