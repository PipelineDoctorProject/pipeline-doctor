from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    failure_type = Column(String, nullable=False)
    finding_type = Column(String)  
    finding_id = Column(Integer)
    severity = Column(String, nullable=False)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("PipelineRun", back_populates="incidents")
    remediation_runs = relationship(
        "RemediationRun",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
