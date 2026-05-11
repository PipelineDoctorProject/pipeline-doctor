from sqlalchemy import text

from app.models.tenant_tables import TENANT_MODELS


def create_schema(db, schema_name: str):

    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    # Create schema
    db.execute(
        text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
    )

    db.commit()

    # Dynamically create tenant tables
    for model in TENANT_MODELS:

        model.__table__.schema = schema_name

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