from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.incident_report import IncidentReport
from app.models.pipeline_run import PipelineRun


def create_incident_report_version(
    db: Session,
    *,
    incident: Incident,
    rca_payload: dict[str, Any],
    generator: str = "deterministic",
    generator_model: str | None = None,
) -> IncidentReport:
    content = build_incident_report_content(incident=incident, rca_payload=rca_payload)
    evidence_hash = _stable_hash(content.get("source_evidence", {}))

    latest_version = (
        db.query(IncidentReport.version)
        .filter(IncidentReport.incident_id == incident.id)
        .order_by(IncidentReport.version.desc())
        .first()
    )
    next_version = (latest_version[0] if latest_version else 0) + 1

    report = IncidentReport(
        incident_id=incident.id,
        run_id=incident.run_id,
        version=next_version,
        status="ready",
        report_type="incident_rca",
        title=content["title"],
        executive_summary=content["executive_summary"],
        narrative=content["narrative"],
        evidence_hash=evidence_hash,
        generator=generator,
        generator_model=generator_model,
        content=content,
    )
    db.add(report)
    db.flush()
    return report


def build_incident_report_content(
    *,
    incident: Incident,
    rca_payload: dict[str, Any],
) -> dict[str, Any]:
    final_report = _dict(rca_payload.get("final_report"))
    remediation = _dict(rca_payload.get("remediation"))
    issues = _list(rca_payload.get("issues"))
    evidence = _list(rca_payload.get("evidence"))
    failure_types = _list(rca_payload.get("failure_types"))
    severity = rca_payload.get("severity") or incident.severity
    report_title = final_report.get("report_title") or rca_payload.get("title") or incident.title
    run = incident.run
    model = run.model if isinstance(run, PipelineRun) and run.model else None

    executive_summary = (
        final_report.get("incident_summary")
        or rca_payload.get("summary")
        or "OpsSight detected a production monitoring incident for this pipeline run."
    )
    recommendation = (
        final_report.get("recommended_action")
        or remediation.get("recommended_action")
        or rca_payload.get("recommendation")
        or "Review the evidence, validate the source data, and approve remediation only if the change is expected."
    )
    root_cause = (
        final_report.get("root_cause_summary")
        or rca_payload.get("reasoning")
        or rca_payload.get("summary")
        or "Root cause reasoning was generated from stored monitoring evidence."
    )

    timeline = _build_timeline(incident, final_report)
    findings = _build_findings(issues, evidence)
    remediation_section = _build_remediation_section(remediation, final_report)
    risk = _build_risk_assessment(severity, failure_types, remediation)
    narrative = _build_narrative(
        executive_summary=executive_summary,
        root_cause=root_cause,
        recommendation=recommendation,
        severity=severity,
        remediation=remediation_section,
    )

    return {
        "title": report_title,
        "generated_at": datetime.utcnow().isoformat(),
        "executive_summary": executive_summary,
        "narrative": narrative,
        "severity": severity,
        "status": incident.status,
        "model_context": {
            "model_id": getattr(model, "id", None),
            "model_name": getattr(model, "name", None),
            "model_version": getattr(model, "version", None),
            "framework": getattr(model, "framework", None),
            "training_mode": getattr(model, "training_mode", None),
            "mlflow_model_name": getattr(model, "mlflow_model_name", None),
            "mlflow_alias": getattr(model, "mlflow_alias", None),
        },
        "run_context": {
            "run_id": incident.run_id,
            "baseline_version": getattr(run, "baseline_version", None),
            "status": getattr(run, "status", None),
            "created_at": _iso(getattr(run, "created_at", None)),
            "input_file_path": getattr(run, "file_path", None),
            "cleaned_data_path": getattr(run, "cleaned_data_path", None),
        },
        "timeline": timeline,
        "root_cause": {
            "summary": root_cause,
            "failure_types": failure_types,
            "provider": rca_payload.get("provider"),
            "model": rca_payload.get("model"),
        },
        "findings": findings,
        "remediation": remediation_section,
        "risk_assessment": risk,
        "next_actions": _build_next_actions(recommendation, remediation_section),
        "appendix": {
            "raw_evidence_count": len(evidence),
            "raw_issue_count": len(issues),
            "evidence": evidence,
            "issues": issues,
        },
        "source_evidence": {
            "incident_id": incident.id,
            "run_id": incident.run_id,
            "failure_types": failure_types,
            "severity": severity,
            "issues": issues,
            "evidence": evidence,
            "remediation": remediation,
            "final_report": final_report,
        },
    }


def _build_timeline(incident: Incident, final_report: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "label": "Incident created",
            "time": _iso(incident.created_at),
            "detail": "Monitoring converted severe signals into an incident.",
        },
        {
            "label": "RCA completed",
            "time": final_report.get("generated_at") or _iso(incident.created_at),
            "detail": final_report.get("timeline_summary")
            or "Detection completed, AI reasoning finished, and the final report was saved.",
        },
    ]


def _build_findings(
    issues: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_items = issues or evidence
    findings = []
    for item in source_items[:12]:
        title = item.get("title") or item.get("type") or item.get("feature") or item.get("column") or "Finding"
        findings.append(
            {
                "title": title,
                "severity": item.get("severity") or "unknown",
                "summary": item.get("summary") or item.get("explanation") or item.get("details") or "",
                "affected_columns": item.get("affected_columns") or [item.get("column") or item.get("feature")],
                "recommended_action": item.get("recommended_action"),
                "evidence_count": item.get("evidence_count"),
            }
        )
    return findings


def _build_remediation_section(
    remediation: dict[str, Any],
    final_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "action_type": final_report.get("action_type") or remediation.get("action_type"),
        "action_mode": final_report.get("action_mode") or remediation.get("action_mode"),
        "requires_approval": bool(final_report.get("requires_approval") or remediation.get("requires_approval")),
        "manual_action_required": bool(final_report.get("manual_action_required") or remediation.get("manual_only")),
        "report_status": final_report.get("report_status"),
        "action_taken": final_report.get("action_taken"),
        "candidate_model_uri": remediation.get("candidate_model_uri"),
        "staged_model_uri": remediation.get("staged_model_uri"),
        "deployed_model_uri": remediation.get("deployed_model_uri"),
        "latest_status": remediation.get("last_status"),
    }


def _build_risk_assessment(
    severity: str,
    failure_types: list[Any],
    remediation: dict[str, Any],
) -> dict[str, Any]:
    normalized = str(severity or "medium").lower()
    if normalized in {"critical", "high"}:
        posture = "Do not promote or refresh production baselines until the evidence is reviewed."
    else:
        posture = "Review the monitoring evidence and continue if the shift is expected."

    return {
        "severity": normalized,
        "risk_level": "production-impacting" if normalized in {"critical", "high"} else "watch",
        "primary_risks": [str(item) for item in failure_types[:6]],
        "safety_posture": posture,
        "deployment_guardrail": "Champion alias is only updated after staging review and deployment confirmation.",
        "remediation_status": remediation.get("last_status") or remediation.get("action_mode"),
    }


def _build_next_actions(
    recommendation: str,
    remediation: dict[str, Any],
) -> list[str]:
    actions = [recommendation]
    if remediation.get("requires_approval"):
        actions.append("Review the remediation approval console before creating or staging a candidate model.")
    if remediation.get("staged_model_uri"):
        actions.append("Deploy the staged model through the customer deployment pipeline, then confirm deployment in OpsSight.")
    if remediation.get("manual_action_required"):
        actions.append("Keep the incident open until the owner documents the manual investigation outcome.")
    return actions


def _build_narrative(
    *,
    executive_summary: str,
    root_cause: str,
    recommendation: str,
    severity: str,
    remediation: dict[str, Any],
) -> str:
    action_status = remediation.get("report_status") or "not_started"
    return (
        f"{executive_summary}\n\n"
        f"Root cause analysis: {root_cause}\n\n"
        f"Current severity is {severity}. The remediation lifecycle status is {action_status}. "
        "OpsSight keeps monitoring evidence as the source of truth and uses the narrative report only to explain that evidence.\n\n"
        f"Recommended next step: {recommendation}"
    )


def _stable_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _iso(value: Any) -> str | None:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return None
