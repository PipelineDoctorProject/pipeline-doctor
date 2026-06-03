from __future__ import annotations

import json
from typing import Any

from app.models.incident import Incident
from app.models.remediation_run import RemediationRun


def sync_incident_remediation_state(
    incident: Incident,
    remediation_run: RemediationRun,
    *,
    status: str,
    message: str | None = None,
    result: dict[str, Any] | None = None,
    target_column: str | None = None,
) -> None:
    payload = _parse_payload(incident.description)
    remediation = payload.get("remediation") if isinstance(payload.get("remediation"), dict) else {}
    final_report = payload.get("final_report") if isinstance(payload.get("final_report"), dict) else {}

    remediation_message = message or remediation_run.result_summary or ""
    normalized_status = str(status or "").lower()
    remediation.update(
        {
            "last_run_id": remediation_run.id,
            "last_status": normalized_status,
            "last_message": remediation_message,
            "target_column": target_column or remediation.get("target_column"),
            "candidate_pending_promotion": normalized_status in {"pending_promotion", "completed"},
            "candidate_review_status": normalized_status,
        }
    )

    if result:
        remediation["candidate_metrics"] = result.get("metrics")
        remediation["candidate_model_uri"] = result.get("candidate_model_uri")
        remediation["candidate_mlflow_run_id"] = result.get("candidate_mlflow_run_id")
        remediation["feature_columns"] = result.get("feature_columns")
        remediation["feature_source"] = result.get("feature_source")
        remediation["staged_model_uri"] = result.get("staged_model_uri")
        remediation["staged_model_version"] = result.get("staged_model_version")
        remediation["staged_model_name"] = result.get("staged_model_name")
        remediation["staged_alias"] = result.get("staged_alias")
        remediation["promoted_model_uri"] = result.get("promoted_model_uri")
        remediation["promoted_model_version"] = result.get("promoted_model_version")
        remediation["promoted_model_name"] = result.get("promoted_model_name")
        remediation["promoted_alias"] = result.get("promoted_alias")
        remediation["review_notes"] = result.get("review_notes")
        remediation["promoted_by"] = result.get("promoted_by")
        remediation["deployment_required"] = result.get("deployment_required")
        remediation["deployed_alias"] = result.get("deployed_alias")
        remediation["deployed_model_uri"] = result.get("deployed_model_uri")
        remediation["deployment_status"] = result.get("deployment_status")
        remediation["deployed_by"] = result.get("deployed_by")

    report_updates = _build_final_report_updates(status, remediation_message, result)
    final_report.update(report_updates)
    payload["remediation"] = remediation
    payload["final_report"] = final_report
    incident.description = json.dumps(payload, default=str)


def _parse_payload(description: str | None) -> dict[str, Any]:
    if not description:
        return {}

    try:
        payload = json.loads(description)
    except json.JSONDecodeError:
        return {}

    return payload if isinstance(payload, dict) else {}


def _build_final_report_updates(
    status: str,
    message: str,
    result: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_status = str(status or "").lower()
    candidate_metrics = (result or {}).get("metrics")
    staged_alias = (result or {}).get("staged_alias") or (result or {}).get("promoted_alias")
    staged_version = (
        (result or {}).get("staged_model_version")
        or (result or {}).get("promoted_model_version")
    )

    if normalized_status == "queued":
        return {
            "report_status": "queued_for_execution",
            "action_taken": "Remediation was approved and queued for execution.",
            "manual_action_required": True,
            "timeline_summary": "Detection completed, AI reasoning finished, approval was granted, and remediation was queued.",
        }

    if normalized_status == "running":
        return {
            "report_status": "remediation_running",
            "action_taken": "Approved remediation is running in the background.",
            "manual_action_required": True,
            "timeline_summary": "Detection completed, AI reasoning finished, approval was granted, and remediation is currently running.",
        }

    if normalized_status == "rejected":
        return {
            "report_status": "remediation_rejected",
            "action_taken": "Remediation was rejected before execution.",
            "manual_action_required": True,
            "timeline_summary": "Detection completed, AI reasoning finished, and the prepared remediation was rejected.",
        }

    if normalized_status == "cancel_requested":
        return {
            "report_status": "remediation_cancel_requested",
            "action_taken": "Cancellation was requested for the running remediation.",
            "manual_action_required": True,
            "timeline_summary": "Detection completed, AI reasoning finished, remediation started, and cancellation was requested.",
        }

    if normalized_status == "canceled":
        return {
            "report_status": "remediation_canceled",
            "action_taken": "Remediation execution was canceled before candidate promotion.",
            "manual_action_required": True,
            "timeline_summary": "Detection completed, AI reasoning finished, remediation started, and execution was canceled before promotion.",
        }

    if normalized_status == "blocked":
        return {
            "report_status": "remediation_blocked",
            "action_taken": "Remediation was blocked by policy or a missing prerequisite.",
            "manual_action_required": True,
            "timeline_summary": "Detection completed, AI reasoning finished, but remediation was blocked before execution.",
        }

    if normalized_status == "failed":
        return {
            "report_status": "remediation_failed",
            "action_taken": "Remediation execution failed before a candidate model could be finalized.",
            "manual_action_required": True,
            "timeline_summary": f"Detection completed, AI reasoning finished, remediation started, and execution failed: {message}",
        }

    if normalized_status in {"pending_promotion", "completed"}:
        metric_summary = ""
        if candidate_metrics:
            formatted = ", ".join(
                f"{metric}={value:.4f}" if isinstance(value, (int, float)) else f"{metric}={value}"
                for metric, value in candidate_metrics.items()
            )
            metric_summary = f" Candidate metrics: {formatted}."

        return {
            "report_status": "candidate_ready_for_review",
            "action_taken": "Candidate retraining completed and now requires human review before promotion.",
            "manual_action_required": True,
            "timeline_summary": (
                "Detection completed, AI reasoning finished, remediation executed, and a candidate model was produced for review."
                + metric_summary
            ),
        }

    if normalized_status == "staged":
        alias_summary = (
            f" as alias '{staged_alias}'"
            if staged_alias
            else ""
        )
        version_summary = (
            f" version {staged_version}"
            if staged_version
            else ""
        )
        return {
            "report_status": "candidate_staged_for_deployment",
            "action_taken": "Candidate model was approved and staged for deployment.",
            "manual_action_required": True,
            "timeline_summary": (
                "Detection completed, AI reasoning finished, remediation executed, candidate review passed,"
                f" and the candidate was staged{alias_summary}{version_summary}. Deployment confirmation is still required."
            ),
        }

    if normalized_status == "deployed":
        deployed_alias = (result or {}).get("deployed_alias") or staged_alias
        deployed_uri = (result or {}).get("deployed_model_uri")
        return {
            "report_status": "remediation_deployed",
            "action_taken": "Deployment was confirmed and the champion alias was updated.",
            "manual_action_required": False,
            "timeline_summary": (
                "Detection completed, AI reasoning finished, remediation executed, candidate review passed,"
                f" deployment was confirmed, and active monitoring now tracks alias '{deployed_alias}'."
                + (f" Model URI: {deployed_uri}." if deployed_uri else "")
            ),
        }

    if normalized_status == "promotion_rejected":
        return {
            "report_status": "candidate_rejected",
            "action_taken": "Candidate model was reviewed and rejected; the existing live model remains active.",
            "manual_action_required": True,
            "timeline_summary": (
                "Detection completed, AI reasoning finished, remediation executed, and the candidate model was rejected during human review."
            ),
        }

    return {}
