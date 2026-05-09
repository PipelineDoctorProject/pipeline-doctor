from pydantic import BaseModel
from datetime import datetime

# #Runs
class RunCreate(BaseModel):
    status: str
    drift_score: float

class RunResponse(BaseModel):
    id: int
    status: str
    drift_score: float
    created_at: datetime
    
    
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
    
    