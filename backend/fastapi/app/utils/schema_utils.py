from sqlalchemy import text

from app.models.tenant_tables import TENANT_MODELS


def create_schema(db, schema_name: str):

    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    # Create schema and switch to it
    db.execute(
        text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
    )
    db.execute(
        text(f'SET search_path TO "{schema_name}"')
    )
    db.commit()

    # Dynamically create tenant tables in the specific schema
    for model in TENANT_MODELS:
        # We don't modify model.__table__.schema globally.
        # Instead, we just ensure the table exists in the current search_path.
        model.__table__.create(
            bind=db.bind,
            checkfirst=True
        )

    db.commit()


def set_schema(db, schema_name: str):

    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    db.execute(
        text(f'SET search_path TO "{schema_name}", public')
    )