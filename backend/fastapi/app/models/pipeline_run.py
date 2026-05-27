from sqlalchemy import Column, Integer, DateTime, String, ForeignKey,Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    baseline_version = Column(Integer, nullable=False)

    file_path = Column(String, nullable=True)


    cleaned_data_path = Column(String, nullable=True)


    predictions = relationship("PredictionLog", back_populates="run")

    status = Column(String, default="running")

    created_at = Column(DateTime, default=datetime.utcnow)

    cleaned_data_path = Column(String, nullable=True)

    model = relationship("MLModel", back_populates="runs")

    findings = relationship("DataQualityFinding", back_populates="run")


    schema_changed = Column(Boolean, default=False)
    drift_findings = relationship("DriftFinding", back_populates="run")  # ADD THIS
    incidents = relationship("Incident",back_populates='run')
    incident_groups = relationship("IncidentGroup", back_populates="run")


    drift_findings = relationship("DriftFinding", back_populates="run")

    incidents = relationship("Incident", back_populates="run")

