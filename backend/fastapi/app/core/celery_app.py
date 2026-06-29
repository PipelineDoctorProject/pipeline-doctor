import os
import ssl

from celery import Celery
from celery.schedules import crontab
from app.config.settings import REDIS_URL


celery = Celery(
    "opssight",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.scheduler_tasks",
        "app.tasks.remediation_tasks",
    ],
)

celery.conf.update(

    # =========================
    # SERIALIZATION
    # =========================
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # =========================
    # TIMEZONE
    # =========================
    timezone="UTC",
    enable_utc=True,

    # =========================
    # RELIABILITY
    # =========================
    task_track_started=True,
    broker_connection_retry_on_startup=True,

    task_acks_late=True,
    task_reject_on_worker_lost=True,

    worker_prefetch_multiplier=1,

    # =========================
    # ROUTING
    # =========================
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.ai_tasks.*": {"queue": "ai"},
        "app.tasks.remediation_tasks.*": {"queue": "remediation"},
        "app.tasks.scheduler_tasks.*": {"queue": "scheduler"},
    },

    # =========================
    # CELERY BEAT
    # =========================
    beat_schedule={
        "doctor-monitoring-every-minute": {
            "task": "app.tasks.scheduler_tasks.trigger_doctor_monitoring",
            "schedule": crontab(minute="*/1"),  # change to 1 min for demo
            "options": {"expires": 50},
        },
        "beat-heartbeat-every-minute": {
            "task": "app.tasks.scheduler_tasks.record_beat_heartbeat",
            "schedule": crontab(minute="*/1"),
            "options": {"expires": 50},
        },
    },
)

# Redis Cloud uses rediss:// (TLS). The sync redis client does not honour
# ?ssl_cert_reqs=none in the URL, so we must pass the SSL options explicitly
# to both the broker and the result backend to avoid certificate errors.
if REDIS_URL.startswith("rediss://"):
    # Build an SSL context identical to the one used by the async Redis
    # client (_make_async_redis in agent_trace.py). Passing ssl_context
    # directly bypasses kombu's own SSL wiring, which does not correctly
    # apply CERT_NONE via the dict-based broker_use_ssl on Python 3.12.
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE
    _ssl_opts = {"ssl_context": _ssl_ctx}
    celery.conf.update(
        broker_use_ssl=_ssl_opts,
        redis_backend_use_ssl=_ssl_opts,
    )


if os.name == "nt":
    celery.conf.worker_pool = "solo"
    celery.conf.worker_concurrency = 1
