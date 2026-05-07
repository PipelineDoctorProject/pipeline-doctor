from sqlalchemy import Column, Integer, JSON, DateTime, String, Boolean
from datetime import datetime

from app.models.base import Base

from app.db.base import Base



class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, nullable=False)

    version = Column(Integer, nullable=False)

    schema = Column(JSON, nullable=False)
    profile = Column(JSON, nullable=False)

    status = Column(String, default="draft")  # draft / approved
    is_active = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)