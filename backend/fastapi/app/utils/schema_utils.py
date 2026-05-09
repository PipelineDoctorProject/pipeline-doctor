from sqlalchemy import text

def create_schema(db, schema_name: str):
    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    db.commit()


def set_schema(db, schema_name: str):
    # Basic validation (important for safety)
    if not schema_name.isidentifier():
        raise ValueError("Invalid schema name")

    db.execute(text(f'SET search_path TO "{schema_name}"'))