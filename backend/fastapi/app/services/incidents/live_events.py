import json
from datetime import datetime

import redis
from app.config.settings import REDIS_URL

INCIDENTS_CHANNEL = "incidents"


def _serialize_incident(incident):
    created_at = incident.created_at
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()

    return {
        "id": incident.id,
        "run_id": incident.run_id,
        "title": incident.title,
        "failure_type": incident.failure_type,
        "finding_type": incident.finding_type,
        "finding_id": incident.finding_id,
        "severity": incident.severity,
        "status": incident.status,
        "created_at": created_at,
    }


def publish_incident_event(event_type: str, incident):
    try:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        client.publish(
            INCIDENTS_CHANNEL,
            json.dumps(
                {
                    "event": event_type,
                    "incident": _serialize_incident(incident),
                }
            ),
        )
        client.close()
    except Exception:
        # Incident persistence should not fail because realtime delivery is unavailable.
        pass
