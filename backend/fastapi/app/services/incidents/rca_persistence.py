import json

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.services.incidents.live_events import publish_incident_event


def persist_root_cause_incident(db: Session, run_id: int, root_cause_state):
    report = root_cause_state.get("report") or {}
    failure_types = report.get("failure_types") or []

    if not failure_types:
        return None

    payload = {
        "title": report.get("title") or "AI Root Cause Analysis",
        "provider": root_cause_state.get("llm_provider"),
        "model": root_cause_state.get("llm_model"),
        "summary": report.get("summary"),
        "recommendation": report.get("recommendation"),
        "failure_types": failure_types,
        "severity": report.get("severity"),
        "issues": report.get("issues", []),
        "evidence": report.get("evidence", []),
        "reasoning": root_cause_state.get("llm_reasoning"),
    }

    incident = (
        db.query(Incident)
        .filter(
            Incident.run_id == run_id,
            Incident.failure_type == "ai_root_cause",
            Incident.finding_type == "root_cause",
        )
        .first()
    )

    if not incident:
        incident = Incident(
            run_id=run_id,
            title="AI Root Cause Analysis",
            description="",
            failure_type="ai_root_cause",
            finding_type="root_cause",
            finding_id=None,
            severity=report.get("severity", "medium"),
            status="open",
        )
        db.add(incident)

    incident.title = "AI Root Cause Analysis"
    incident.description = json.dumps(payload, default=str)
    incident.severity = report.get("severity", "medium")
    db.commit()
    db.refresh(incident)
    publish_incident_event("incident_updated", incident)
    return incident
