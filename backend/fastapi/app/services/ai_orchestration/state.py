from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed through Detection -> Reasoning -> Reporting."""

    run_id: int
    model_id: int
    baseline_version: int

    schema_change_detected: bool
    extra_columns: List[str]
    missing_columns: List[str]
    validation_result: Dict[str, Any]

    dq_findings: List[Dict[str, Any]]
    drift_findings: List[Dict[str, Any]]
    detected_signals: List[Dict[str, Any]]

    root_cause_prompt: str
    llm_provider: str
    llm_model: str
    llm_reasoning: str
    parsed_failure_types: List[str]
    severity: str

    report: Dict[str, Any]
    errors: List[str]
