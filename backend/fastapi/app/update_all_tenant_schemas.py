from app.db.session import SessionLocal
from app.utils.schema_utils import create_schema

from app.models.tenant import Tenant


db = SessionLocal()

try:

    tenants = db.query(Tenant).all()

    for tenant in tenants:

        if tenant.schema_name:

            print(
                f"Updating schema: {tenant.schema_name}"
            )

            create_schema(
                db,
                tenant.schema_name
            )

    print("All tenant schemas updated")

finally:

    db.close()