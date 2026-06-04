from datetime import datetime
from typing import Any

from pydantic import BaseModel


class IncidentReportSummary(BaseModel):
    id: int
    incident_id: int
    run_id: int
    version: int
    status: str
    report_type: str
    title: str
    executive_summary: str
    generator: str
    generator_model: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentReportResponse(IncidentReportSummary):
    narrative: str
    evidence_hash: str
    content: dict[str, Any]
