from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    input_data = Column(JSON, nullable=False)
    prediction = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    run = relationship("PipelineRun", back_populates="predictions")