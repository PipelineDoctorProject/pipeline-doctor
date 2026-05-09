"""merge heads

Revision ID: 275bd4b1b642
Revises: 9d4184ba85f0, ced99619193d
Create Date: 2026-05-08 15:55:28.085006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '275bd4b1b642'
down_revision: Union[str, Sequence[str], None] = ('9d4184ba85f0', 'ced99619193d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
