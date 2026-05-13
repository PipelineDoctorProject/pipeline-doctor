from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DriftResponse(BaseModel):
    id: int
    run_id: int
    feature_name: str
    drift_score: float
    drift_detected: bool
    psi_score: Optional[float] = None
    ks_score: Optional[float] = None
    ks_pvalue: Optional[float] = None
    severity: str
    created_at: datetime

    class Config:
        orm_mode = True
