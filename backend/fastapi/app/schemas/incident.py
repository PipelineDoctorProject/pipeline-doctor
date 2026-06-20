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
    report_title: Optional[str] = None
    incident_summary: Optional[str] = None
    root_cause_summary: Optional[str] = None
    evidence_summary: Optional[str] = None
    recommended_action: Optional[str] = None
    action_taken: Optional[str] = None
    manual_action_required: Optional[bool] = None
    report_status: Optional[str] = None
    severity: Optional[str] = None
    timeline_summary: Optional[str] = None
    action_type: Optional[str] = None
    action_mode: Optional[str] = None
    requires_approval: Optional[bool] = None
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
    group_id: Optional[int] = None
    child_incident_count: int = 1
    is_primary_incident: bool = True
    group_title: Optional[str] = None
    group_summary: Optional[str] = None
    guidance: Optional[dict[str, Any]] = None
    rca_report: Optional[dict[str, Any]] = None
    remediation: Optional[RemediationSummary] = None
    final_report: Optional[FinalReportSummary] = None
    
    class Config:
        from_attributes = True
