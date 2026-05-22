from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional

class IncidentCreate(BaseModel):
    run_id :int
    title: str
    description:str
    failure_type:str
    severity: str


class IncidentResponse(BaseModel):
    id:int
    run_id:int
    title:str
    description:str
    failure_type:str
    severity:str
    status:str
    created_at:datetime
    finding_type: Optional[str] = None
    finding_id: Optional[int] = None
    guidance: Optional[dict[str, Any]] = None
    rca_report: Optional[dict[str, Any]] = None
    
    class Config:
        from_attributes = True
