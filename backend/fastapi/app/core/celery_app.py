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

# Redis Cloud uses rediss:// (TLS). kombu does not pass ssl_context
# through to redis-py 7.x correctly. Strategy:
# 1. Use individual SSL kwargs in broker_use_ssl (kombu understands these).
# 2. Monkey-patch redis.connection.SSLConnection.__init__ to REPLACE the
#    SSL context redis-py builds internally with ssl.create_default_context()
#    — the same context we use for the async client which is known to work.
if REDIS_URL.startswith("rediss://"):
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE

    # Patch SSLConnection so every sync redis connection uses our context.
    try:
        from redis.connection import SSLConnection as _SSLCls
        _orig_ssl_init = _SSLCls.__init__
        _ctx_ref = _ssl_ctx

        def _patched_ssl_init(self, *args, **kwargs):
            _orig_ssl_init(self, *args, **kwargs)
            # Replace whatever context redis-py built with ours.
            self.ssl_context = _ctx_ref

        _SSLCls.__init__ = _patched_ssl_init
    except Exception:
        pass  # If patching fails, fall back to broker_use_ssl kwargs below.

    # Also tell kombu to enable SSL (individual kwargs are recognised).
    _ssl_opts = {"ssl_cert_reqs": ssl.CERT_NONE, "ssl_check_hostname": False}
    celery.conf.update(
        broker_use_ssl=_ssl_opts,
        redis_backend_use_ssl=_ssl_opts,
    )


if os.name == "nt":
    celery.conf.worker_pool = "solo"
    celery.conf.worker_concurrency = 1
