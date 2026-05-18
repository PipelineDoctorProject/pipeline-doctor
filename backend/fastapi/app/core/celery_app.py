from celery import Celery

celery = Celery(
    "opssight",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.tasks.email_tasks"],
)

celery.conf.update(

    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    timezone="UTC",
    enable_utc=True,

    task_track_started=True,

    broker_connection_retry_on_startup=True,

    task_routes={
        "app.tasks.email_tasks.*": {
            "queue": "emails"
        }
    },

    worker_prefetch_multiplier=1,

    task_acks_late=True,

    task_reject_on_worker_lost=True,
)