from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base


class AgentStepLog(Base):
    __tablename__ = "agent_step_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)

    step_index = Column(Integer, nullable=False)
    log_type = Column(String, nullable=False)  # e.g. chain_of_thought, action, evidence
    message = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    agent_run = relationship("AgentRun", back_populates="steps")