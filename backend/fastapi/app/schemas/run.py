from pydantic import BaseModel
from datetime import datetime

# #Runs
class RunCreate(BaseModel):
    status: str
    drift_score: float

from typing import Optional

class MLModelSummary(BaseModel):
    id: int
    name: str
    version: str

    class Config:
        orm_mode = True

class RunResponse(BaseModel):
    id: int
    model_id: int
    baseline_version: int
    status: str
    created_at: datetime
    schema_changed: Optional[bool] = False
    model: Optional[MLModelSummary] = None

    class Config:
        orm_mode = True
    
    
class PipeLineCreate(BaseModel):
    model_id:int
    mode:str
    # status:str
    # model:str
    
    
class PipeLineResponse(BaseModel):
    id:int
    model_id:int
    status:str
    started_at:datetime
    
    