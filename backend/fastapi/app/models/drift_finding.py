from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from sqlalchemy import Boolean
from datetime import datetime
from sqlalchemy import DateTime

class DriftFinding(Base):
    __tablename__ = "drift_findings"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    
    feature_name = Column(String, nullable=False)
    drift_score = Column(Float, nullable=False)
    drift_detected = Column(Boolean, default=False)
    psi_score = Column(Float, nullable=True)
    ks_score = Column(Float, nullable=True)
    ks_pvalue = Column(Float, nullable=True)
    severity = Column(String, default="low")
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("PipelineRun", back_populates="drift_findings")