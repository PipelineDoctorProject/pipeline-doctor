from sqlalchemy import Column, Integer, String, ForeignKey,Boolean,DateTime,JSON
from sqlalchemy.orm import relationship
from app.models.base import Base

class DataQualityFinding(Base):
    __tablename__ = "data_quality_findings"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer)
    pipeline_run_id = Column(Integer, ForeignKey('pipeline_runs.id'))

    column_name = Column(String)
    check_type = Column(String)
    success = Column(Boolean)

    details = Column(JSON)
    created_at = Column(DateTime)
    
    