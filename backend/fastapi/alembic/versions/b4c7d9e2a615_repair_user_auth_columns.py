"""repair user auth columns

Revision ID: b4c7d9e2a615
Revises: 91db8c2e7a64
Create Date: 2026-06-04 11:25:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b4c7d9e2a615"
down_revision: Union[str, Sequence[str], None] = "91db8c2e7a64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ensure user auth columns exist after historical branch migrations."""
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS invite_token VARCHAR")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS invite_accepted BOOLEAN")
    op.execute("UPDATE users SET role = COALESCE(role, 'admin')")
    op.execute("UPDATE users SET invite_accepted = COALESCE(invite_accepted, TRUE)")


def downgrade() -> None:
    """Keep auth columns on downgrade to avoid breaking login."""
    pass
