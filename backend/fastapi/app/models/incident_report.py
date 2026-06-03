from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="ready")
    report_type = Column(String, nullable=False, default="incident_rca")
    title = Column(String, nullable=False)
    executive_summary = Column(Text, nullable=False)
    narrative = Column(Text, nullable=False)
    evidence_hash = Column(String, nullable=False)
    generator = Column(String, nullable=False, default="deterministic")
    generator_model = Column(String, nullable=True)
    content = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="reports")
    run = relationship("PipelineRun", back_populates="incident_reports")
