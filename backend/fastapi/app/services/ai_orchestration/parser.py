import json
import re
from typing import Any, Dict, Iterable, List


FAILURE_TYPES = {
    "DATA_DRIFT",
    "CONCEPT_DRIFT",
    "SCHEMA_MISMATCH",
    "MISSING_COLUMNS",
    "EXTRA_COLUMNS",
    "NULL_SPIKE",
    "RANGE_VIOLATION",
    "CATEGORICAL_SHIFT",
    "DATA_QUALITY",
}

SEVERITY_ORDER = ["low", "medium", "high", "critical"]

KEYWORD_RULES = {
    "DATA_DRIFT": ["data_drift", "data drift", "psi", "population stability", "feature drift"],
    "CONCEPT_DRIFT": ["concept_drift", "concept drift", "prediction_output", "prediction output", "model output"],
    "SCHEMA_MISMATCH": ["schema_type_mismatch", "type mismatch", "expected", "got"],
    "MISSING_COLUMNS": ["missing_columns", "missing columns", "missing column"],
    "EXTRA_COLUMNS": ["extra_columns", "extra columns", "new columns"],
    "NULL_SPIKE": ["null_ratio", "null spike", "missing data"],
    "RANGE_VIOLATION": ["range", "outside", "out of range"],
    "CATEGORICAL_SHIFT": ["categorical", "unseen"],
}


def parse_root_cause_response(text: str) -> Dict[str, Any]:
    payload = _extract_json_payload(text)
    if "failure_types" in payload:
        failure_types = _normalize_failure_types(payload["failure_types"])
    else:
        failure_types = classify_failure_types(text)

    severity = _normalize_severity(payload.get("severity")) or infer_severity(text)

    return {
        "failure_types": failure_types,
        "severity": severity,
        "summary": payload.get("summary") or _first_sentence(text),
        "recommendation": payload.get("recommendation") or "Review the flagged checks and compare the current batch against the active baseline.",
    }


def classify_failure_types(text: str) -> List[str]:
    haystack = text.lower()
    matches = []
    for failure_type, keywords in KEYWORD_RULES.items():
        if any(keyword in haystack for keyword in keywords):
            matches.append(failure_type)

    # Strip JSON keys to avoid matching 'fail' inside 'failure_types'
    cleaned_text = re.sub(r'"\w+":', "", haystack)
    if not matches and ("fail" in cleaned_text or "quality" in cleaned_text):
        matches.append("DATA_QUALITY")

    return matches


def infer_severity(text: str) -> str:
    haystack = text.lower()
    for severity in reversed(SEVERITY_ORDER):
        if severity in haystack:
            return severity
    return "medium"


def max_severity(values: Iterable[str]) -> str:
    best = "low"
    for value in values:
        severity = _normalize_severity(value)
        if severity and SEVERITY_ORDER.index(severity) > SEVERITY_ORDER.index(best):
            best = severity
    return best


def _extract_json_payload(text: str) -> Dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = [fenced.group(1)] if fenced else []

    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidates.append(text[first : last + 1])

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            continue

    return {}


def _normalize_failure_types(values: Any) -> List[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []

    normalized = []
    for value in values:
        key = str(value).strip().upper().replace(" ", "_").replace("-", "_")
        if key in FAILURE_TYPES and key not in normalized:
            normalized.append(key)
    return normalized


def _normalize_severity(value: Any) -> str:
    if value is None:
        return ""
    severity = str(value).strip().lower()
    return severity if severity in SEVERITY_ORDER else ""


def _first_sentence(text: str) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return "No root-cause reasoning was produced."
    return cleaned.split(". ", 1)[0][:240]
