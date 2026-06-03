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

    _repair_incident_group_run_fk(db, schema_name)
    _repair_remediation_fks(db, schema_name)
    _repair_schema_change_event_columns(db, schema_name)
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


def _repair_incident_group_run_fk(db: Session, schema_name: str) -> None:
    fk_row = db.execute(
        text(
            """
            SELECT
                c.conname AS fk_name,
                ref_ns.nspname AS ref_schema,
                ref_tbl.relname AS ref_table
            FROM pg_constraint c
            JOIN pg_class src_tbl ON src_tbl.oid = c.conrelid
            JOIN pg_namespace src_ns ON src_ns.oid = src_tbl.relnamespace
            JOIN pg_class ref_tbl ON ref_tbl.oid = c.confrelid
            JOIN pg_namespace ref_ns ON ref_ns.oid = ref_tbl.relnamespace
            WHERE c.contype = 'f'
              AND src_ns.nspname = :schema_name
              AND src_tbl.relname = 'incident_groups'
              AND c.conname = 'incident_groups_run_id_fkey'
            """
        ),
        {"schema_name": schema_name},
    ).mappings().first()

    if not fk_row:
        return

    if fk_row["ref_schema"] == schema_name and fk_row["ref_table"] == "pipeline_runs":
        return

    db.execute(
        text(
            f'ALTER TABLE "{schema_name}".incident_groups '
            "DROP CONSTRAINT IF EXISTS incident_groups_run_id_fkey"
        )
    )
    # Legacy rows may have been grouped using public.pipeline_runs ids.
    # Ungroup those incident references, then remove stale groups so
    # the tenant-local FK can be added safely.
    db.execute(
        text(
            f"""
            UPDATE "{schema_name}".incidents
            SET group_id = NULL
            WHERE group_id IN (
                SELECT ig.id
                FROM "{schema_name}".incident_groups ig
                LEFT JOIN "{schema_name}".pipeline_runs pr ON pr.id = ig.run_id
                WHERE pr.id IS NULL
            )
            """
        )
    )
    db.execute(
        text(
            f"""
            DELETE FROM "{schema_name}".incident_groups ig
            WHERE NOT EXISTS (
                SELECT 1
                FROM "{schema_name}".pipeline_runs pr
                WHERE pr.id = ig.run_id
            )
            """
        )
    )
    db.execute(
        text(
            f'ALTER TABLE "{schema_name}".incident_groups '
            f'ADD CONSTRAINT incident_groups_run_id_fkey '
            f'FOREIGN KEY (run_id) REFERENCES "{schema_name}".pipeline_runs(id)'
        )
    )


def _repair_remediation_fks(db: Session, schema_name: str) -> None:
    _repair_simple_tenant_fk(
        db=db,
        schema_name=schema_name,
        src_table="remediation_runs",
        src_column="incident_id",
        fk_name="remediation_runs_incident_id_fkey",
        ref_table="incidents",
    )


def _repair_schema_change_event_columns(db: Session, schema_name: str) -> None:
    db.execute(
        text(
            f'ALTER TABLE "{schema_name}".schema_change_events '
            "ADD COLUMN IF NOT EXISTS feature_candidates JSON"
        )
    )
    db.execute(
        text(
            f'ALTER TABLE "{schema_name}".schema_change_events '
            "ADD COLUMN IF NOT EXISTS feature_decisions JSON"
        )
    )
    _repair_simple_tenant_fk(
        db=db,
        schema_name=schema_name,
        src_table="remediation_runs",
        src_column="run_id",
        fk_name="remediation_runs_run_id_fkey",
        ref_table="pipeline_runs",
    )
    _repair_simple_tenant_fk(
        db=db,
        schema_name=schema_name,
        src_table="remediation_action_logs",
        src_column="remediation_run_id",
        fk_name="remediation_action_logs_remediation_run_id_fkey",
        ref_table="remediation_runs",
    )


def _repair_simple_tenant_fk(
    db: Session,
    schema_name: str,
    src_table: str,
    src_column: str,
    fk_name: str,
    ref_table: str,
) -> None:
    fk_row = db.execute(
        text(
            """
            SELECT
                c.conname AS fk_name,
                ref_ns.nspname AS ref_schema,
                ref_tbl.relname AS ref_table
            FROM pg_constraint c
            JOIN pg_class src_tbl ON src_tbl.oid = c.conrelid
            JOIN pg_namespace src_ns ON src_ns.oid = src_tbl.relnamespace
            JOIN pg_class ref_tbl ON ref_tbl.oid = c.confrelid
            JOIN pg_namespace ref_ns ON ref_ns.oid = ref_tbl.relnamespace
            WHERE c.contype = 'f'
              AND src_ns.nspname = :schema_name
              AND src_tbl.relname = :src_table
              AND c.conname = :fk_name
            """
        ),
        {
            "schema_name": schema_name,
            "src_table": src_table,
            "fk_name": fk_name,
        },
    ).mappings().first()

    if not fk_row:
        return

    if fk_row["ref_schema"] == schema_name and fk_row["ref_table"] == ref_table:
        return

    db.execute(
        text(
            f'ALTER TABLE "{schema_name}".{src_table} '
            f"DROP CONSTRAINT IF EXISTS {fk_name}"
        )
    )
    db.execute(
        text(
            f"""
            DELETE FROM "{schema_name}".{src_table} src
            WHERE NOT EXISTS (
                SELECT 1
                FROM "{schema_name}".{ref_table} ref
                WHERE ref.id = src.{src_column}
            )
            """
        )
    )
    db.execute(
        text(
            f'ALTER TABLE "{schema_name}".{src_table} '
            f"ADD CONSTRAINT {fk_name} "
            f'FOREIGN KEY ({src_column}) REFERENCES "{schema_name}".{ref_table}(id)'
        )
    )
