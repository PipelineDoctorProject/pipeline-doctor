import json
import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from app.api.routes.health import celery_health_check


def main() -> int:
    report = celery_health_check()

    print("Celery Stack Health")
    print(json.dumps(report, indent=2, default=str))
    print()

    worker = report.get("worker", {})
    beat = report.get("beat", {})

    if report.get("status") == "healthy":
        print("Result: healthy")
        return 0

    print("Result: degraded")

    missing_queues = worker.get("missing_queues") or []
    if missing_queues:
        print(f"Missing queues: {', '.join(missing_queues)}")

    if not beat.get("healthy"):
        print("Beat heartbeat missing or stale.")

    print("Recommended worker command:")
    print(r".\venv\Scripts\celery.exe -A app.core.celery_app:celery worker -Q ai,scheduler,emails -l info")
    print("Recommended beat command:")
    print(r".\venv\Scripts\celery.exe -A app.core.celery_app:celery beat -l info")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
