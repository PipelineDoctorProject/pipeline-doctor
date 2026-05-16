"""final merge

Revision ID: b771d77d183c
Revises: 8d07f90d91a3, b29fa65f1dcd
Create Date: 2026-05-12 15:08:08.871932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b771d77d183c'
down_revision: Union[str, Sequence[str], None] = ('8d07f90d91a3', 'b29fa65f1dcd')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
