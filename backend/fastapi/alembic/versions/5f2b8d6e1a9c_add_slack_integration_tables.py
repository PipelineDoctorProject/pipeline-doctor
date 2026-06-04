"""add slack integration tables

Revision ID: 5f2b8d6e1a9c
Revises: b771d77d183c
Create Date: 2026-05-24 20:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "5f2b8d6e1a9c"
down_revision = "b771d77d183c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "slack_workspaces" not in inspector.get_table_names():
        op.create_table(
            "slack_workspaces",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("slack_team_id", sa.String(), nullable=False),
            sa.Column("slack_team_name", sa.String(), nullable=False),
            sa.Column("bot_token", sa.String(), nullable=False),
            sa.Column("bot_user_id", sa.String(), nullable=True),
            sa.Column("scope", sa.String(), nullable=True),
            sa.Column("connected_by_user_id", sa.String(), nullable=True),
            sa.Column("connected_by_slack_user_id", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["connected_by_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slack_team_id"),
            sa.UniqueConstraint("tenant_id"),
        )

    if "slack_channels" not in inspector.get_table_names():
        op.create_table(
            "slack_channels",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("workspace_id", sa.String(), nullable=False),
            sa.Column("slack_channel_id", sa.String(), nullable=False),
            sa.Column("slack_channel_name", sa.String(), nullable=False),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["slack_workspaces.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("workspace_id", "slack_channel_id", name="uq_slack_workspace_channel"),
        )


def downgrade() -> None:
    op.drop_table("slack_channels")
    op.drop_table("slack_workspaces")
