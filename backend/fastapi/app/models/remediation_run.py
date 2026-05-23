from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class RemediationRun(Base):
    __tablename__ = "remediation_runs"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    tenant_id = Column(String, nullable=True)
    action_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending_approval")
    trigger_mode = Column(String, nullable=False, default="policy")
    created_by = Column(String, nullable=True)
    result_summary = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="remediation_runs")
    action_logs = relationship(
        "RemediationActionLog",
        back_populates="remediation_run",
        cascade="all, delete-orphan",
    )
