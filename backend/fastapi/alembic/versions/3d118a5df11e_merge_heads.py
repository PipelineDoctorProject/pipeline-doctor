"""merge heads

Revision ID: 3d118a5df11e
Revises: 5f2b8d6e1a9c, a8f4e2d1c301
Create Date: 2026-05-25 14:05:13.164551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d118a5df11e'
down_revision: Union[str, Sequence[str], None] = ('5f2b8d6e1a9c', 'a8f4e2d1c301')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
