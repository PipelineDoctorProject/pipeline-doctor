from pydantic import BaseModel, ConfigDict
from typing import Any, Optional
from datetime import datetime

class DriftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    interpretation: Optional[dict[str, Any]] = None

