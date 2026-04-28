from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    framework = Column(String, default="sklearn")
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("PipelineRun", back_populates="model")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    status = Column(String, default="running")
    drift_score = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    model = relationship("MLModel", back_populates="runs")
    predictions = relationship("PredictionLog", back_populates="run")
    incidents = relationship("Incident", back_populates="run")


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    input_data = Column(JSON, nullable=False)
    prediction = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("PipelineRun", back_populates="predictions")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    failure_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("PipelineRun", back_populates="incidents")