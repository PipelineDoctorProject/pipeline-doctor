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
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("PipelineRun", back_populates="model")