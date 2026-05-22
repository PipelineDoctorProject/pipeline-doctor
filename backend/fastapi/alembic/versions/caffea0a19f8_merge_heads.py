"""merge heads

Revision ID: caffea0a19f8
Revises: 5ce83cf6eb23, 6e9893f5e93f
Create Date: 2026-05-07 16:53:09.178144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'caffea0a19f8'
down_revision: Union[str, Sequence[str], None] = ('5ce83cf6eb23', '6e9893f5e93f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
