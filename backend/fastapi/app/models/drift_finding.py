from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class DriftFinding(Base):
    __tablename__ = "drift_findings"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    
    feature_name = Column(String, nullable=False)
    drift_score = Column(Float, nullable=False)
    drift_detected = Column(String, default="no")  # yes/no or enum

    run = relationship("PipelineRun", back_populates="drift_findings")