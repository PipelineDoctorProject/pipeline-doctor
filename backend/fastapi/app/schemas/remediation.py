from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RemediationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    run_id: int
    tenant_id: str | None = None
    action_type: str
    status: str
    trigger_mode: str
    created_by: str | None = None
    result_summary: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


class RemediationDecisionResponse(BaseModel):
    id: int
    status: str
    action_type: str | None = None
    message: str


class RemediationActionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remediation_run_id: int
    step_name: str
    status: str
    message: str
    payload: dict | None = None
    created_at: datetime


class RemediationContextResponse(BaseModel):
    incident_id: int
    run_id: int
    model_id: int
    model_name: str | None = None
    model_framework: str | None = None
    expected_features: list[str] = []
    expected_features_source: str | None = None
    dataset_columns: list[str] = []
    target_candidates: list[str] = []
    suggested_target_column: str | None = None
    cleaned_data_available: bool
    readiness_warnings: list[str] = []
