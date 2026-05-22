import os

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


if os.name == "nt":
    celery.conf.worker_pool = "solo"
    celery.conf.worker_concurrency = 1
