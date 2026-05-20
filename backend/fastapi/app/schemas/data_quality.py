from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class DataQualityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: int
    pipeline_run_id: int
    column_name: Optional[str] = None
    check_type: str
    success: bool
    details: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None    # Optional — handles existing rows without timestamps

