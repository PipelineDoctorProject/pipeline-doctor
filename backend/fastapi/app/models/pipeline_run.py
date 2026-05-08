from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base




class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)


    model = relationship("MLModel", back_populates="runs")
    predictions = relationship("PredictionLog", back_populates="run", cascade="all, delete")
    incidents = relationship("Incident", back_populates="run", cascade="all, delete")
    drift_findings = relationship("DriftFinding", back_populates="run", cascade="all, delete")
    data_quality_findings = relationship("DataQualityFinding", back_populates="run", cascade="all, delete") 

    model_id = Column(Integer, nullable=False)
    baseline_version = Column(Integer, nullable=False)

    file_path = Column(String, nullable=True)

    status = Column(String, default="running")  # running / success / failed

    created_at = Column(DateTime, default=datetime.utcnow)

