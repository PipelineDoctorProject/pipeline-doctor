import json
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.incident_group import IncidentGroup


SEVERITY_RANK = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def ensure_incident_group(
    db: Session,
    *,
    run_id: int,
) -> IncidentGroup:
    group = (
        db.query(IncidentGroup)
        .filter(IncidentGroup.run_id == run_id)
        .first()
    )
    if group:
        return group

    group = IncidentGroup(
        run_id=run_id,
        title=f"Run {run_id} monitoring alert",
        summary="Monitoring detected one or more signals for this run.",
        severity="medium",
        status="open",
    )
    db.add(group)
    db.flush()
    return group


def attach_incident_to_group(
    db: Session,
    *,
    incident: Incident,
    group: IncidentGroup | None = None,
) -> IncidentGroup:
    group = group or ensure_incident_group(db, run_id=incident.run_id)
    incident.group = group
    db.flush()
    refresh_incident_group(db, group)
    return group


def refresh_incident_group(db: Session, group: IncidentGroup) -> IncidentGroup:
    incidents = (
        db.query(Incident)
        .filter(Incident.group_id == group.id)
        .order_by(Incident.created_at.asc(), Incident.id.asc())
        .all()
    )

    if not incidents:
        group.title = f"Run {group.run_id} monitoring alert"
        group.summary = "No grouped incident evidence is currently attached."
        group.severity = "medium"
        group.status = "open"
        group.primary_incident_id = None
        db.flush()
        return group

    primary = _choose_primary_incident(incidents)
    group.primary_incident_id = primary.id
    group.title = _group_title(primary)
    group.summary = _group_summary(primary, incidents)
    group.severity = _max_severity(incident.severity for incident in incidents)
    group.status = _group_status(incidents)
    db.flush()
    return group


def backfill_incident_groups_for_run(db: Session, run_id: int) -> IncidentGroup | None:
    incidents = (
        db.query(Incident)
        .filter(Incident.run_id == run_id)
        .order_by(Incident.created_at.asc(), Incident.id.asc())
        .all()
    )
    if not incidents:
        return None

    group = ensure_incident_group(db, run_id=run_id)
    for incident in incidents:
        incident.group = group

    db.flush()
    return refresh_incident_group(db, group)


def _choose_primary_incident(incidents: list[Incident]) -> Incident:
    rca_incident = next(
        (incident for incident in reversed(incidents) if incident.failure_type == "ai_root_cause"),
        None,
    )
    if rca_incident:
        return rca_incident

    return max(
        incidents,
        key=lambda incident: (
            SEVERITY_RANK.get(incident.severity or "low", 0),
            incident.created_at,
            incident.id,
        ),
    )


def _group_title(primary: Incident) -> str:
    if primary.failure_type == "ai_root_cause":
        return primary.title or f"Run {primary.run_id} root cause alert"
    return f"Run {primary.run_id} monitoring alert"


def _group_summary(primary: Incident, incidents: list[Incident]) -> str:
    rca_payload = _parse_payload(primary.description)
    if rca_payload:
        return (
            rca_payload.get("summary")
            or rca_payload.get("recommendation")
            or primary.description
        )

    unique_failure_types = sorted({
        incident.failure_type
        for incident in incidents
        if incident.failure_type
    })
    summary = primary.description or f"{len(incidents)} monitoring incident(s) detected."
    summary = " ".join(str(summary).split())

    if unique_failure_types:
        type_label = ", ".join(unique_failure_types[:4])
        return f"{summary} Signals: {type_label}."

    return summary


def _group_status(incidents: Iterable[Incident]) -> str:
    statuses = {incident.status for incident in incidents if incident.status}
    if "open" in statuses:
        return "open"
    if "investigating" in statuses:
        return "investigating"
    return next(iter(statuses), "open")


def _max_severity(severities: Iterable[str]) -> str:
    best = "low"
    for severity in severities:
        if SEVERITY_RANK.get(severity or "low", 0) > SEVERITY_RANK.get(best, 0):
            best = severity
    return best


def _parse_payload(description: str | None) -> dict | None:
    if not description:
        return None
    try:
        payload = json.loads(description)
    except (TypeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None
