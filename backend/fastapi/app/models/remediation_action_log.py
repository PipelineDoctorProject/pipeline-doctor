from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class RemediationActionLog(Base):
    __tablename__ = "remediation_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    remediation_run_id = Column(Integer, ForeignKey("remediation_runs.id"), nullable=False)
    step_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    remediation_run = relationship("RemediationRun", back_populates="action_logs")
