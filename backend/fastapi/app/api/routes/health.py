import json
from datetime import datetime, timezone

import redis
from fastapi import APIRouter

from app.config.settings import REDIS_URL
from app.core.celery_app import celery

router = APIRouter()
INSPECT_TIMEOUT_SECONDS = 5

@router.get("/health")
def health_check():
    return {"status": "PipelineDoctor is running"}


@router.get("/health/celery")
def celery_health_check():
    now = datetime.now(timezone.utc)
    redis_ok = False
    heartbeat = None
    heartbeat_age_seconds = None
    heartbeat_ok = False
    redis_error = None

    client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        redis_ok = bool(client.ping())
        raw_heartbeat = client.get("celery:beat:last_heartbeat")
        if raw_heartbeat:
            heartbeat = json.loads(raw_heartbeat)
            timestamp_value = heartbeat.get("timestamp_utc")
            if timestamp_value:
                heartbeat_at = datetime.fromisoformat(timestamp_value)
                heartbeat_age_seconds = round((now - heartbeat_at).total_seconds(), 2)
                heartbeat_ok = heartbeat_age_seconds <= 120
    except Exception as exc:
        redis_error = str(exc)
    finally:
        client.close()

    inspector = celery.control.inspect(timeout=INSPECT_TIMEOUT_SECONDS)
    workers = inspector.ping() or {}
    queues_by_worker = inspector.active_queues() or {}

    worker_names = sorted(workers.keys())
    queue_names = sorted({
        queue.get("name")
        for worker_queues in queues_by_worker.values()
        for queue in worker_queues
        if queue.get("name")
    })
    required_queues = ["ai", "scheduler"]
    missing_queues = [
        queue_name
        for queue_name in required_queues
        if queue_name not in queue_names
    ]

    overall_ok = redis_ok and bool(worker_names) and heartbeat_ok and not missing_queues

    return {
        "status": "healthy" if overall_ok else "degraded",
        "redis": {
            "url": REDIS_URL,
            "connected": redis_ok,
            "error": redis_error,
        },
        "worker": {
            "online": bool(worker_names),
            "count": len(worker_names),
            "workers": worker_names,
            "queues": queue_names,
            "required_queues": required_queues,
            "missing_queues": missing_queues,
            "inspect_timeout_seconds": INSPECT_TIMEOUT_SECONDS,
            "ping": workers,
        },
        "beat": {
            "schedule_entries": sorted(celery.conf.beat_schedule.keys()),
            "last_heartbeat": heartbeat,
            "heartbeat_age_seconds": heartbeat_age_seconds,
            "healthy": heartbeat_ok,
        },
        "frontend": {
            "cors_origin": "http://localhost:5173",
            "websocket_path": "/ws/agent-trace/{run_id}",
            "trace_events_source": "Redis pub/sub via FastAPI WebSocket bridge",
        },
    }
