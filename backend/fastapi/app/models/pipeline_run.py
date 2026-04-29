from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    status = Column(String, default="running")
    drift_score = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    model = relationship("MLModel", back_populates="runs")
    predictions = relationship("PredictionLog", back_populates="run")
    incidents = relationship("Incident", back_populates="run")
    drift_findings = relationship("DriftFinding", back_populates="run")
    data_quality_findings = relationship("DataQualityFinding", back_populates="run")