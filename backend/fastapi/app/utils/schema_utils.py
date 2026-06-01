from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models.tenant_tables import TENANT_MODELS


def create_schema(db, schema_name: str):

    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    # Create schema and use tenant-first resolution while still allowing
    # tenant tables to reference shared public tables such as public.tenants.
    db.execute(
        text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
    )
    db.execute(
        text(f'SET search_path TO "{schema_name}", public')
    )

    connection = db.connection()
    inspector = inspect(connection)

    # Dynamically create tenant tables in the specific schema.
    # We must check existence in the tenant schema explicitly; otherwise
    # public tables on the search_path can fool SQLAlchemy into skipping
    # creation for a broken tenant schema.
    for model in TENANT_MODELS:
        table = model.__table__
        if inspector.has_table(table.name, schema=schema_name):
            continue

        # Use the same connection where search_path was set so unqualified
        # foreign keys resolve against tenant tables first and public shared
        # tables second.
        table.create(
            bind=connection,
            checkfirst=False
        )

    db.commit()


def set_schema(db, schema_name: str):

    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    db.info["schema_name"] = schema_name
    db.execute(
        text(f'SET search_path TO "{schema_name}", public')
    )


def apply_session_schema(session, connection):
    schema_name = session.info.get("schema_name")

    if not schema_name:
        return

    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    connection.execute(
        text(f'SET search_path TO "{schema_name}", public')
    )


def ensure_all_tenant_schemas(db: Session, tenants) -> list[str]:
    repaired_schemas: list[str] = []

    for tenant in tenants:
        schema_name = getattr(tenant, "schema_name", None)
        if not schema_name:
            continue

        create_schema(db, schema_name)
        repaired_schemas.append(schema_name)

    return repaired_schemas
