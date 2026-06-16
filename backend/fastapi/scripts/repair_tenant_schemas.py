import os
import sys
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.utils.schema_utils import ensure_all_tenant_schemas


def repair_tenant_schemas(max_attempts: int = 5):
    last_error = None

    for attempt in range(1, max_attempts + 1):
        db = SessionLocal()
        try:
            db.info.pop("schema_name", None)
            db.execute(text("SET search_path TO public"))

            tenants = db.query(Tenant).order_by(Tenant.schema_name.asc()).all()
            if not tenants:
                print("No tenants found. Nothing to repair.")
                return []

            repaired_schemas = ensure_all_tenant_schemas(db, tenants)
            print(f"Tenant schema repair completed for {len(repaired_schemas)} schema(s).")
            for schema_name in repaired_schemas:
                print(f"- {schema_name}")
            return repaired_schemas
        except OperationalError as exc:
            last_error = exc
            print(f"Database connection failed on attempt {attempt}/{max_attempts}: {exc}")
            time.sleep(3)
        finally:
            db.close()

    raise last_error


if __name__ == "__main__":
    repair_tenant_schemas()
