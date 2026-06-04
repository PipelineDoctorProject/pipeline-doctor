"""add incident reports

Revision ID: 6c9f3a1b8d21
Revises: 5f2b8d6e1a9c
Create Date: 2026-06-03 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "6c9f3a1b8d21"
down_revision: Union[str, Sequence[str], None] = "5f2b8d6e1a9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incident_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(), nullable=False, server_default="ready"),
        sa.Column("report_type", sa.String(), nullable=False, server_default="incident_rca"),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("executive_summary", sa.Text(), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column("evidence_hash", sa.String(), nullable=False),
        sa.Column("generator", sa.String(), nullable=False, server_default="deterministic"),
        sa.Column("generator_model", sa.String(), nullable=True),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["pipeline_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incident_reports_id", "incident_reports", ["id"])
    op.create_index("ix_incident_reports_incident_id", "incident_reports", ["incident_id"])
    op.create_index("ix_incident_reports_run_id", "incident_reports", ["run_id"])
    op.create_index(
        "ix_incident_reports_incident_version",
        "incident_reports",
        ["incident_id", "version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_incident_reports_incident_version", table_name="incident_reports")
    op.drop_index("ix_incident_reports_run_id", table_name="incident_reports")
    op.drop_index("ix_incident_reports_incident_id", table_name="incident_reports")
    op.drop_index("ix_incident_reports_id", table_name="incident_reports")
    op.drop_table("incident_reports")
