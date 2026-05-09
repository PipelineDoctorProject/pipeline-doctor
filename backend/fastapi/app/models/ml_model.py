from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    framework = Column(String, default="sklearn")
    mlflow_model_name = Column(String, nullable=True)
    mlflow_alias = Column(String, nullable=True)
    mlflow_run_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    runs = relationship("PipelineRun", back_populates="model")