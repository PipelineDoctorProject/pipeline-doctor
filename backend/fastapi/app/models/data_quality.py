from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class DataQualityFinding(Base):
    __tablename__ = "data_quality_findings"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)

    issue_type = Column(String, nullable=False)  # missing, outlier, schema
    column_name = Column(String, nullable=False)
    description = Column(String)

    run = relationship("PipelineRun", back_populates="data_quality_findings")