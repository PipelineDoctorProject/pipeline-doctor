from pydantic import BaseModel, ConfigDict
from datetime import datetime

# #Runs
class RunCreate(BaseModel):
    status: str
    drift_score: float

from typing import Optional

class MLModelSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    version: str

class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: int
    baseline_version: int
    status: str
    created_at: datetime
    schema_changed: Optional[bool] = False
    model: Optional[MLModelSummary] = None

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
    
    
