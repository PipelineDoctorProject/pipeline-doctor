from typing import Any


def build_final_incident_report(
    root_cause_state: dict[str, Any],
    remediation_policy: dict[str, Any],
) -> dict[str, Any]:
    report = root_cause_state.get("report") or {}
    evidence = report.get("evidence") or []
    failure_types = report.get("failure_types") or []

    action_mode = remediation_policy.get("action_mode") or "none"
    action_type = remediation_policy.get("action_type") or "observe"
    requires_approval = bool(remediation_policy.get("requires_approval"))
    manual_only = bool(remediation_policy.get("manual_only"))

    if manual_only:
        action_taken = "No automated remediation was executed."
        report_status = "manual_action_required"
    elif requires_approval:
        action_taken = "Remediation was prepared but is waiting for human approval."
        report_status = "awaiting_approval"
    else:
        action_taken = "No automated remediation was executed in this flow."
        report_status = "report_ready"

    return {
        "report_title": report.get("title") or "AI Root Cause Analysis",
        "incident_summary": report.get("summary") or "An incident was detected during monitoring.",
        "root_cause_summary": root_cause_state.get("llm_reasoning") or report.get("summary") or "",
        "evidence_summary": _build_evidence_summary(evidence),
        "recommended_action": remediation_policy.get("recommended_action") or report.get("recommendation"),
        "action_taken": action_taken,
        "manual_action_required": manual_only or requires_approval,
        "report_status": report_status,
        "severity": report.get("severity", "medium"),
        "timeline_summary": "Detection completed, AI reasoning finished, output was parsed, and the final report was saved.",
        "action_type": action_type,
        "action_mode": action_mode,
        "requires_approval": requires_approval,
        "failure_types": failure_types,
    }


def _build_evidence_summary(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return "No structured evidence was stored for this incident."

    snippets = []
    for item in evidence[:3]:
        title = item.get("title") or item.get("type") or "signal"
        severity = item.get("severity") or "unknown"
        snippets.append(f"{title} ({severity})")

    return "Primary evidence signals: " + ", ".join(snippets) + "."
