from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class IncidentGroup(Base):
    __tablename__ = "incident_groups"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    severity = Column(String, nullable=False, default="medium")
    status = Column(String, nullable=False, default="open")
    primary_incident_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    run = relationship("PipelineRun", back_populates="incident_groups")
    incidents = relationship(
        "Incident",
        back_populates="group",
        foreign_keys="Incident.group_id",
    )
