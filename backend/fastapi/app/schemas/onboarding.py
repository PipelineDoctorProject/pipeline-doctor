from pydantic import BaseModel


class CompanyOnboardingRequest(BaseModel):
    company_name: str