from sqlalchemy import text

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

    # Dynamically create tenant tables in the specific schema
    for model in TENANT_MODELS:
        # We use 'db.connection()' to ensure the DDL is executed on the same 
        # connection where we just set the search_path.
        model.__table__.create(
            bind=db.connection(),
            checkfirst=True
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
