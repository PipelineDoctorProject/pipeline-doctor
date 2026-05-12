from sqlalchemy import text

from app.models.tenant_tables import TENANT_MODELS


def create_schema(db, schema_name: str):

    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    # Create schema and switch to it (ONLY the tenant schema for now)
    db.execute(
        text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
    )
    db.execute(
        text(f'SET search_path TO "{schema_name}"')
    )

    # Dynamically create tenant tables in the specific schema
    for model in TENANT_MODELS:
        # We use 'db.connection()' to ensure the DDL is executed on the same 
        # connection where we just set the search_path.
        model.__table__.create(
            bind=db.connection(),
            checkfirst=True
        )

    # Now set the search_path to include public for subsequent operations
    db.execute(
        text(f'SET search_path TO "{schema_name}", public')
    )
    db.commit()


def set_schema(db, schema_name: str):

    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    db.execute(
        text(f'SET search_path TO "{schema_name}", public')
    )