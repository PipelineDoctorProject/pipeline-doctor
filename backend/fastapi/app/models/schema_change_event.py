from sqlalchemy import Column, Integer,JSON, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class SchemaChangeEvent(Base):
    __tablename__ = "schema_change_events"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, nullable=False)

    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.id"))
    baseline_id = Column(Integer, ForeignKey("baselines.id"))

    new_columns = Column(JSON)
    missing_columns = Column(JSON)

    status = Column(String, default="pending")  # pending / approved / rejected
    created_at = Column(DateTime, default=datetime.utcnow)