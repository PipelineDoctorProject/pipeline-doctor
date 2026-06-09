from typing import Any


def decide_remediation(
    incident_payload: dict[str, Any] | None,
    root_cause_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    incident_payload = incident_payload or {}
    root_cause_state = root_cause_state or {}

    severity = str(incident_payload.get("severity") or "medium").lower()
    failure_types = [
        str(item).upper()
        for item in (incident_payload.get("failure_types") or [])
        if item
    ]

    if _requires_source_data_correction(failure_types):
        return {
            "recommended_action": (
                "Fix or validate the upstream/incoming data first, then run the DAG again. "
                "Only consider retraining after the follow-up run proves the data contract is clean."
            ),
            "action_type": "manual_data_correction",
            "action_mode": "manual_only",
            "requires_approval": False,
            "allowed_to_execute": False,
            "manual_only": True,
            "reason": (
                "This incident contains source-data quality or schema failures. "
                "Retraining on malformed data is blocked by production safety policy."
            ),
        }

    if severity == "critical":
        return {
            "recommended_action": "Manual investigation required before any model or baseline change.",
            "action_type": "manual_investigation",
            "action_mode": "manual_only",
            "requires_approval": False,
            "allowed_to_execute": False,
            "manual_only": True,
            "reason": "Critical incidents are alert-only in the current production safety policy.",
        }

    if _is_retraining_candidate(failure_types):
        return {
            "recommended_action": "Prepare a controlled retraining run and require admin approval before execution.",
            "action_type": "retrain_model",
            "action_mode": "approval_required",
            "requires_approval": True,
            "allowed_to_execute": True,
            "manual_only": False,
            "reason": "The failure pattern suggests population or concept change that may require model refresh.",
        }

    if severity == "high":
        return {
            "recommended_action": "Review the issue manually and approve a remediation only after validating the source change.",
            "action_type": "manual_review",
            "action_mode": "approval_required",
            "requires_approval": True,
            "allowed_to_execute": False,
            "manual_only": True,
            "reason": "High-severity incidents are not auto-executed without human approval.",
        }

    if severity == "medium":
        return {
            "recommended_action": "Investigate the incident and refresh the baseline only if the shift is confirmed as expected.",
            "action_type": "review_and_refresh_baseline",
            "action_mode": "suggestion_only",
            "requires_approval": False,
            "allowed_to_execute": False,
            "manual_only": True,
            "reason": "Medium-severity incidents only prepare remediation guidance in the current MVP.",
        }

    return {
        "recommended_action": "No immediate remediation is required. Keep monitoring future runs.",
        "action_type": "observe",
        "action_mode": "none",
        "requires_approval": False,
        "allowed_to_execute": False,
        "manual_only": False,
        "reason": "Low-severity incidents should not trigger remediation execution.",
    }


def _is_retraining_candidate(failure_types: list[str]) -> bool:
    retraining_signals = {
        "DATA_DRIFT",
        "CONCEPT_DRIFT",
        "MODEL_DEGRADATION",
    }
    return any(signal in retraining_signals for signal in failure_types)


def _requires_source_data_correction(failure_types: list[str]) -> bool:
    source_data_failures = {
        "SCHEMA_MISMATCH",
        "MISSING_COLUMNS",
        "EXTRA_COLUMNS",
        "DATA_QUALITY",
        "NULL_SPIKE",
        "RANGE_VIOLATION",
        "CATEGORICAL_SHIFT",
    }
    return any(signal in source_data_failures for signal in failure_types)
