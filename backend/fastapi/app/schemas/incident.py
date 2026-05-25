from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional


class IncidentCreate(BaseModel):
    run_id :int
    title: str
    description:str
    failure_type:str
    severity: str


class RemediationSummary(BaseModel):
    recommended_action: str
    action_type: str
    action_mode: str
    requires_approval: bool
    allowed_to_execute: bool
    manual_only: bool
    reason: str


class FinalReportSummary(BaseModel):
    report_title: str
    incident_summary: str
    root_cause_summary: str
    evidence_summary: str
    recommended_action: Optional[str] = None
    action_taken: str
    manual_action_required: bool
    report_status: str
    severity: str
    timeline_summary: str
    action_type: str
    action_mode: str
    requires_approval: bool
    failure_types: list[str] = []


class IncidentResponse(BaseModel):
    id:int
    run_id:int
    title:str
    description:str
    failure_type:str
    severity:str
    status:str
    created_at:datetime
    finding_type: Optional[str] = None
    finding_id: Optional[int] = None
    guidance: Optional[dict[str, Any]] = None
    rca_report: Optional[dict[str, Any]] = None
    remediation: Optional[RemediationSummary] = None
    final_report: Optional[FinalReportSummary] = None
    
    class Config:
        from_attributes = True
