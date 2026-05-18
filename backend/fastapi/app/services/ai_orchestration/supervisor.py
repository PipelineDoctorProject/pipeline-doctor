import json
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.data_quality import DataQualityFinding
from app.models.drift_finding import DriftFinding
from app.models.pipeline_run import PipelineRun
from app.services.ai_orchestration.llm_client import (
    get_configured_model_name,
    get_default_llm_callable,
)
from app.services.ai_orchestration.parser import (
    classify_failure_types,
    max_severity,
    parse_root_cause_response,
)
from app.services.ai_orchestration.prompts import build_root_cause_prompt
from app.services.ai_orchestration.state import AgentState

try:
    from langgraph.graph import END, StateGraph
except ImportError:
    END = None
    StateGraph = None


LLMCallable = Callable[[str], str]
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def build_supervisor_graph(db: Session, llm: Optional[LLMCallable] = None):
    if StateGraph is None:
        return _SequentialSupervisor(db, llm)

    graph = StateGraph(AgentState)
    graph.add_node("detection", lambda state: _detection_node(db, state))
    graph.add_node("reasoning", lambda state: _reasoning_node(state, llm))
    graph.add_node("parser", _parser_node)
    graph.add_node("reporting", _reporting_node)

    graph.set_entry_point("detection")
    graph.add_edge("detection", "reasoning")
    graph.add_edge("reasoning", "parser")
    graph.add_edge("parser", "reporting")
    graph.add_edge("reporting", END)
    return graph.compile()


def run_root_cause_analysis(
    db: Session,
    run: PipelineRun,
    validation_result: Optional[Dict[str, Any]] = None,
    schema_change_detected: bool = False,
    extra_columns: Optional[List[str]] = None,
    missing_columns: Optional[List[str]] = None,
    llm: Optional[LLMCallable] = None,
) -> AgentState:
    initial_state: AgentState = {
        "run_id": run.id,
        "model_id": run.model_id,
        "baseline_version": run.baseline_version,
        "schema_change_detected": schema_change_detected,
        "extra_columns": extra_columns or [],
        "missing_columns": missing_columns or [],
        "validation_result": validation_result or {},
        "errors": [],
    }
    return build_supervisor_graph(db, llm).invoke(initial_state)


class _SequentialSupervisor:
    def __init__(self, db: Session, llm: Optional[LLMCallable] = None):
        self.db = db
        self.llm = llm

    def invoke(self, state: AgentState) -> AgentState:
        state = _detection_node(self.db, state)
        state = _reasoning_node(state, self.llm)
        state = _parser_node(state)
        return _reporting_node(state)


def _detection_node(db: Session, state: AgentState) -> AgentState:
    run_id = state["run_id"]

    dq_findings = (
        db.query(DataQualityFinding)
        .filter(DataQualityFinding.pipeline_run_id == run_id)
        .all()
    )
    drift_findings = (
        db.query(DriftFinding)
        .filter(DriftFinding.run_id == run_id)
        .all()
    )

    state["dq_findings"] = [_serialize_dq_finding(finding) for finding in dq_findings]
    state["drift_findings"] = [_serialize_drift_finding(finding) for finding in drift_findings]
    state["detected_signals"] = _build_detected_signals(state)
    return state


def _reasoning_node(state: AgentState, llm: Optional[LLMCallable]) -> AgentState:
    prompt = build_root_cause_prompt(state)
    state["root_cause_prompt"] = prompt

    llm_callable = llm or get_default_llm_callable()

    if llm_callable:
        state["llm_provider"] = "groq" if llm is None else "custom"
        state["llm_model"] = get_configured_model_name() or "custom"
        state["llm_reasoning"] = llm_callable(prompt)
    else:
        state["llm_provider"] = "fallback"
        state["llm_model"] = "deterministic-rules"
        state["llm_reasoning"] = _fallback_reasoning(state)

    return state


def _parser_node(state: AgentState) -> AgentState:
    parsed = parse_root_cause_response(state.get("llm_reasoning", ""))

    signal_severity = max_severity(
        signal.get("severity", "low") for signal in state.get("detected_signals", [])
    )
    parsed_severity = parsed["severity"]
    severity = max_severity([signal_severity, parsed_severity])

    state["parsed_failure_types"] = parsed["failure_types"]
    state["severity"] = severity
    state["report"] = {
        "failure_types": parsed["failure_types"],
        "severity": severity,
        "summary": parsed["summary"],
        "recommendation": parsed["recommendation"],
    }
    return state


def _reporting_node(state: AgentState) -> AgentState:
    report = state.get("report", {})
    failure_types = report.get("failure_types", [])
    detected_signals = state.get("detected_signals", [])
    issues = _build_issue_findings(detected_signals)

    if not failure_types:
        state["report"] = {
            "title": "No AI Root Cause Incident",
            "failure_types": [],
            "severity": "low",
            "summary": "No failed detection signals required RCA reporting.",
            "recommendation": "Continue monitoring future runs.",
        }
        return state

    state["report"] = {
        "title": "AI Root Cause Analysis",
        "run_id": state["run_id"],
        "failure_types": failure_types,
        "severity": report.get("severity", "medium"),
        "summary": report.get("summary", ""),
        "recommendation": report.get("recommendation", ""),
        "issues": issues,
        "evidence": detected_signals,
    }
    return state


def _build_detected_signals(state: AgentState) -> List[Dict[str, Any]]:
    signals = []

    if state.get("extra_columns"):
        signals.append({
            "source": "schema",
            "type": "extra_columns",
            "columns": state["extra_columns"],
            "severity": "medium",
            "title": "New columns appeared in the incoming dataset",
            "explanation": "The file contains columns that are not part of the active baseline schema.",
            "likely_cause": "A producer added fields, or the wrong file version was uploaded.",
            "recommended_action": "Approve the schema change only if these columns are expected; otherwise ask the upstream producer to restore the contract.",
        })

    if state.get("missing_columns"):
        signals.append({
            "source": "schema",
            "type": "missing_columns",
            "columns": state["missing_columns"],
            "severity": "high",
            "title": "Required baseline columns are missing",
            "explanation": "The model or downstream pipeline may not receive features it expects.",
            "likely_cause": "A producer removed or renamed fields, or the wrong export was uploaded.",
            "recommended_action": "Block prediction until the missing columns are restored or a new model/baseline is approved.",
        })

    for finding in state.get("dq_findings", []):
        if finding.get("success") is False:
            signal = {
                "source": "data_quality",
                "type": finding.get("check_type"),
                "column": finding.get("column_name"),
                "details": finding.get("details"),
                "severity": _dq_severity(finding.get("check_type")),
            }
            signal.update(_describe_dq_signal(signal))
            signals.append(signal)

    for finding in state.get("drift_findings", []):
        if finding.get("drift_detected"):
            signal = {
                "source": "drift",
                "type": "concept_drift" if finding.get("feature_name") == "prediction_output" else "data_drift",
                "feature": finding.get("feature_name"),
                "psi_score": finding.get("psi_score"),
                "ks_score": finding.get("ks_score"),
                "ks_pvalue": finding.get("ks_pvalue"),
                "drift_score": finding.get("drift_score"),
                "severity": finding.get("severity") or "medium",
            }
            signal.update(_describe_drift_signal(signal))
            signals.append(signal)

    return signals


def _build_issue_findings(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for signal in signals:
        grouped[_issue_group_key(signal)].append(signal)

    issues = []
    for group_key, group_signals in grouped.items():
        severity = max_severity(signal.get("severity", "low") for signal in group_signals)
        columns = sorted({
            value
            for signal in group_signals
            for value in _signal_columns(signal)
            if value
        })
        issues.append({
            "type": group_key,
            "severity": severity,
            "title": _issue_title(group_key, columns),
            "summary": _issue_summary(group_key, group_signals, columns),
            "likely_root_cause": _issue_likely_cause(group_key, group_signals),
            "recommended_action": _issue_recommended_action(group_key),
            "affected_columns": columns,
            "evidence_count": len(group_signals),
            "evidence": group_signals,
        })

    issues.sort(
        key=lambda issue: SEVERITY_RANK.get(issue["severity"], 0),
        reverse=True,
    )
    return issues


def _issue_group_key(signal: Dict[str, Any]) -> str:
    signal_type = signal.get("type")

    if signal_type in {"extra_columns", "missing_columns"}:
        return signal_type

    if signal_type == "schema_type_mismatch":
        return "schema_type_mismatch"

    if signal_type == "null_ratio":
        return "null_spike"

    if signal_type == "range":
        return "range_violation"

    if signal_type == "categorical":
        return "categorical_shift"

    if signal_type in {"data_drift", "concept_drift"}:
        return signal_type

    return signal_type or "data_quality"


def _signal_columns(signal: Dict[str, Any]) -> List[str]:
    values = []

    if signal.get("column"):
        values.append(signal["column"])

    if signal.get("feature"):
        values.append(signal["feature"])

    values.extend(signal.get("columns") or [])
    return values


def _issue_title(group_key: str, columns: List[str]) -> str:
    label = ", ".join(columns[:3])
    suffix = f": {label}" if label else ""

    titles = {
        "schema_type_mismatch": "Column types do not match the baseline",
        "extra_columns": "Unexpected columns were added",
        "missing_columns": "Required columns are missing",
        "null_spike": "Missing values exceeded the quality threshold",
        "range_violation": "Numeric values moved outside the baseline range",
        "categorical_shift": "New categorical values appeared",
        "data_drift": "Feature distributions drifted from the baseline",
        "concept_drift": "Model output distribution drifted",
    }
    return f"{titles.get(group_key, 'Data quality issue')}{suffix}"


def _issue_summary(
    group_key: str,
    signals: List[Dict[str, Any]],
    columns: List[str],
) -> str:
    column_text = ", ".join(columns) if columns else "the dataset"

    if group_key == "range_violation":
        return f"{len(signals)} numeric range check(s) failed for {column_text}."

    if group_key == "categorical_shift":
        unseen = []
        for signal in signals:
            unseen.extend((signal.get("details") or {}).get("unseen_values") or [])
        unseen = sorted(set(unseen))
        return f"Observed unseen category value(s) {unseen[:8]} in {column_text}."

    if group_key == "null_spike":
        return f"Missing-value ratio exceeded the configured threshold for {column_text}."

    if group_key == "schema_type_mismatch":
        return f"Incoming data types are incompatible with the active baseline for {column_text}."

    if group_key == "data_drift":
        max_score = max((signal.get("drift_score") or 0 for signal in signals), default=0)
        return f"Distribution drift was detected for {column_text}; max drift score is {max_score:.3f}."

    if group_key == "concept_drift":
        return "Prediction output distribution changed compared with the reference behavior."

    if group_key == "extra_columns":
        return f"The incoming file includes new column(s): {column_text}."

    if group_key == "missing_columns":
        return f"The incoming file is missing required column(s): {column_text}."

    return f"{len(signals)} issue(s) detected for {column_text}."


def _issue_likely_cause(group_key: str, signals: List[Dict[str, Any]]) -> str:
    causes = {
        "schema_type_mismatch": "The source system changed formatting, introduced invalid tokens, or exported blanks in a way that changed pandas type inference.",
        "extra_columns": "The upstream dataset contract evolved, or a newer/wrong file version was uploaded.",
        "missing_columns": "The upstream export removed or renamed expected fields.",
        "null_spike": "A source extraction problem, mapping issue, or incomplete upstream data load introduced missing values.",
        "range_violation": "The batch contains outliers, unit/currency changes, stale baseline limits, or records from a different population.",
        "categorical_shift": "A new business category/region/status appeared, or category normalization changed upstream.",
        "data_drift": "The current batch distribution differs from the baseline population; this can happen after traffic mix changes, seasonality, or source changes.",
        "concept_drift": "The relationship between features and model output has shifted, or the serving model/data path changed.",
    }
    return causes.get(group_key, "The current batch differs from the active baseline.")


def _issue_recommended_action(group_key: str) -> str:
    actions = {
        "schema_type_mismatch": "Inspect sample bad rows, fix invalid tokens upstream, and keep prediction blocked for affected required features if coercion is unsafe.",
        "extra_columns": "Approve a new baseline only if the columns are expected and downstream consumers are ready for them.",
        "missing_columns": "Restore the missing columns or deploy a compatible model/baseline before using this batch for prediction.",
        "null_spike": "Check ingestion completeness and upstream joins; only rely on imputation if the missingness is expected and monitored.",
        "range_violation": "Review outlier rows and confirm whether the baseline range is stale or the source values are malformed.",
        "categorical_shift": "Confirm whether the new categories are valid business values; update the baseline/category mapping if expected.",
        "data_drift": "Compare the batch source and time window with the baseline, then retrain or refresh the baseline if the population shift is expected.",
        "concept_drift": "Compare model predictions against recent labels and consider retraining if performance has degraded.",
    }
    return actions.get(group_key, "Review the flagged rows and compare them with the active baseline contract.")


def _describe_dq_signal(signal: Dict[str, Any]) -> Dict[str, str]:
    check_type = signal.get("type")
    column = signal.get("column") or "dataset"
    details = signal.get("details") or {}

    if check_type == "range":
        return {
            "title": f"{column} is outside the baseline range",
            "explanation": (
                f"Observed range {details.get('observed_min')}-{details.get('observed_max')} "
                f"versus baseline {details.get('baseline_min')}-{details.get('baseline_max')}."
            ),
            "likely_cause": "Outliers, unit changes, mixed populations, or stale baseline limits.",
            "recommended_action": "Inspect rows above/below the baseline limits and decide whether to fix data or refresh the baseline.",
        }

    if check_type == "categorical":
        return {
            "title": f"{column} contains unseen categories",
            "explanation": f"Unseen values: {details.get('unseen_values') or details.get('info')}.",
            "likely_cause": "New business values appeared, or upstream normalization changed.",
            "recommended_action": "Validate the new category values, then update mappings or baseline if they are expected.",
        }

    if check_type == "null_ratio":
        return {
            "title": f"{column} has too many missing values",
            "explanation": f"Missing ratio {details.get('ratio')} exceeded threshold {details.get('threshold')}.",
            "likely_cause": "Incomplete extraction, broken join, or source field not populated.",
            "recommended_action": "Check upstream completeness before trusting imputed values.",
        }

    if check_type == "schema_type_mismatch":
        return {
            "title": f"{column} has an incompatible type",
            "explanation": details.get("info", "The incoming type differs from the baseline."),
            "likely_cause": "Invalid tokens, formatting change, or a source contract change.",
            "recommended_action": "Inspect raw values that could not be coerced and fix them upstream.",
        }

    return {
        "title": f"{column} failed {check_type}",
        "explanation": details.get("info", "A data quality check failed."),
        "likely_cause": "The incoming batch differs from the active baseline.",
        "recommended_action": "Inspect the affected rows and compare against the source contract.",
    }


def _describe_drift_signal(signal: Dict[str, Any]) -> Dict[str, str]:
    feature = signal.get("feature") or "prediction output"
    psi = signal.get("psi_score")
    ks = signal.get("ks_score")

    if signal.get("type") == "concept_drift":
        return {
            "title": "Prediction output distribution changed",
            "explanation": f"Concept drift signal on {feature}; PSI={psi}, KS={ks}.",
            "likely_cause": "Model behavior shifted because input mix changed or the model/data path changed.",
            "recommended_action": "Compare predictions with labels and review model performance before retraining.",
        }

    return {
        "title": f"{feature} distribution drifted",
        "explanation": f"Current distribution differs from baseline; PSI={psi}, KS={ks}.",
        "likely_cause": "Population mix, seasonality, upstream source changes, or stale baseline data.",
        "recommended_action": "Compare current batch sampling window/source with baseline and refresh baseline only if this shift is expected.",
    }


def _fallback_reasoning(state: AgentState) -> str:
    signals = state.get("detected_signals", [])
    if not signals:
        return """
No failed detection signals were found.
{"failure_types": [], "severity": "low", "summary": "No root-cause incident is required.", "recommendation": "Continue monitoring future runs."}
""".strip()

    text = " ".join(str(signal) for signal in signals)
    failure_types = classify_failure_types(text)
    severity = max_severity(signal.get("severity", "low") for signal in signals)
    summary = f"Detected {len(signals)} pipeline risk signal(s): {', '.join(failure_types) or 'DATA_QUALITY'}."
    recommendation = "Inspect the highest-severity signal first, then update the baseline only if the upstream change is expected."
    payload = {
        "failure_types": failure_types,
        "severity": severity,
        "summary": summary,
        "recommendation": recommendation,
    }

    return f"{summary}\n{json.dumps(payload)}"


def _dq_severity(check_type: str) -> str:
    if check_type in {"missing_columns", "schema_type_mismatch"}:
        return "high"
    if check_type in {"extra_columns", "range", "categorical"}:
        return "medium"
    return "low"


def _serialize_dq_finding(finding: DataQualityFinding) -> Dict[str, Any]:
    return {
        "id": finding.id,
        "model_id": finding.model_id,
        "pipeline_run_id": finding.pipeline_run_id,
        "column_name": finding.column_name,
        "check_type": finding.check_type,
        "success": finding.success,
        "details": finding.details,
    }


def _serialize_drift_finding(finding: DriftFinding) -> Dict[str, Any]:
    return {
        "id": finding.id,
        "run_id": finding.run_id,
        "feature_name": finding.feature_name,
        "drift_score": finding.drift_score,
        "drift_detected": finding.drift_detected,
        "psi_score": finding.psi_score,
        "ks_score": finding.ks_score,
        "ks_pvalue": finding.ks_pvalue,
        "severity": finding.severity,
    }
