from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class MLModelBase(BaseModel):
    name: str
    version: str
    framework: str = "sklearn"
    mlflow_model_name: Optional[str] = None
    mlflow_alias: Optional[str] = None
    mlflow_run_id: Optional[str] = None
    mlflow_tracking_uri: Optional[str] = None
    expected_features: Optional[List[str]] = None

class MLModelCreate(MLModelBase):
    pass

class MLModelResponse(MLModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    registry_status: Optional[str] = None
    registry_message: Optional[str] = None


class DiscoverModelsRequest(BaseModel):
    tracking_uri: str
    

class ModelVersionsRequest(BaseModel):
    tracking_uri: str
    model_name: str


class SetModelAliasRequest(BaseModel):
    version: str
    run_id: str
    alias: str = "champion"

