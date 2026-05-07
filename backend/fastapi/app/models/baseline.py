from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from app.db.base import Base


class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(Integer, primary_key=True, index=True)

    model_id = Column(String, index=True)  # ML model reference

    file_path = Column(String)  # where CSV is stored

    schema = Column(JSON)      # column types
    profile = Column(JSON)     # validation rules

    created_at = Column(DateTime, default=datetime.utcnow)