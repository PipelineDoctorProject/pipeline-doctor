from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import mlflow
from mlflow.tracking import MlflowClient

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
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class DiscoverModelsRequest(BaseModel):
    tracking_uri: str
    

class ModelVersionsRequest(BaseModel):
    tracking_uri: str
    model_name: str