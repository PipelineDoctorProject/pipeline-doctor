import os
import sys
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.incident import Incident
from app.models.incident_group import IncidentGroup
from app.models.tenant import Tenant
from app.services.incidents.grouping import backfill_incident_groups_for_run
from app.utils.schema_utils import set_schema


INCIDENT_GROUP_FK_NAME = "fk_incidents_group_id_incident_groups"
INCIDENT_GROUP_INDEX_NAME = "ix_incidents_group_id"


def backfill_incident_groups():
    last_error = None

    for attempt in range(1, 6):
        db = SessionLocal()
        try:
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

                print(f"Backfilling incident groups for schema: {tenant.schema_name}")
                set_schema(db, tenant.schema_name)

                IncidentGroup.__table__.create(
                    bind=db.connection(),
                    checkfirst=True,
                )

                db.execute(
                    text("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS group_id INTEGER")
                )
                db.execute(
                    text(
                        f"CREATE INDEX IF NOT EXISTS {INCIDENT_GROUP_INDEX_NAME} "
                        "ON incidents (group_id)"
                    )
                )

                fk_exists = db.execute(
                    text(
                        """
                        SELECT 1
                        FROM information_schema.table_constraints
                        WHERE table_schema = current_schema()
                          AND table_name = 'incidents'
                          AND constraint_name = :constraint_name
                        """
                    ),
                    {"constraint_name": INCIDENT_GROUP_FK_NAME},
                ).scalar()

                if not fk_exists:
                    db.execute(
                        text(
                            f"""
                            ALTER TABLE incidents
                            ADD CONSTRAINT {INCIDENT_GROUP_FK_NAME}
                            FOREIGN KEY (group_id) REFERENCES incident_groups (id)
                            """
                        )
                    )

                run_ids = [
                    run_id
                    for (run_id,) in (
                        db.query(Incident.run_id)
                        .distinct()
                        .order_by(Incident.run_id.asc())
                        .all()
                    )
                ]

                for run_id in run_ids:
                    backfill_incident_groups_for_run(db, run_id)

                db.commit()

            print("Incident group backfill completed successfully.")
            return

        except OperationalError as exc:
            last_error = exc
            print(f"Database connection failed on attempt {attempt}/5: {exc}")
            time.sleep(3)
        finally:
            db.close()

    raise last_error


if __name__ == "__main__":
    backfill_incident_groups()
