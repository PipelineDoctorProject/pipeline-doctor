from celery import Celery
from celery.schedules import crontab


celery = Celery(
    "opssight",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
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
        "doctor-monitoring-every-5-min": {
            "task": "app.tasks.scheduler_tasks.trigger_doctor_monitoring",
            "schedule": crontab(minute="*/5"),
        },
    },
)