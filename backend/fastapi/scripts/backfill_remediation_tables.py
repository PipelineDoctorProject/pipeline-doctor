import os
import sys
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.remediation_action_log import RemediationActionLog
from app.models.remediation_run import RemediationRun
from app.models.tenant import Tenant
from app.utils.schema_utils import set_schema


def backfill_remediation_tables():
    last_error = None

    for attempt in range(1, 6):
        db = SessionLocal()
        try:
            # Make sure we read tenants from the shared public schema first.
            db.info.pop("schema_name", None)
            db.execute(text("SET search_path TO public"))

            tenants = (
                db.query(Tenant)
                .order_by(Tenant.schema_name.asc())
                .all()
            )

            if not tenants:
                print("No tenants found. Nothing to backfill.")
                return

            for tenant in tenants:
                if not tenant.schema_name:
                    continue

                print(f"Backfilling remediation tables for schema: {tenant.schema_name}")
                set_schema(db, tenant.schema_name)

                RemediationRun.__table__.create(
                    bind=db.connection(),
                    checkfirst=True,
                )
                RemediationActionLog.__table__.create(
                    bind=db.connection(),
                    checkfirst=True,
                )

                db.commit()

            print("Remediation table backfill completed successfully.")
            return

        except OperationalError as exc:
            last_error = exc
            print(f"Database connection failed on attempt {attempt}/5: {exc}")
            time.sleep(3)
        finally:
            db.close()

    raise last_error


if __name__ == "__main__":
    backfill_remediation_tables()
