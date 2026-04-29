from pydantic import BaseModel
from datetime import datetime

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
    
    class Config:
        from_attributes = True