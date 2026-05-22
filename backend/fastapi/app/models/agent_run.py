from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    tenant_id = Column(String, nullable=True)
    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=True)

    status = Column(String, nullable=False, default="pending")
    result_summary = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    steps = relationship(
        "AgentStepLog",
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )