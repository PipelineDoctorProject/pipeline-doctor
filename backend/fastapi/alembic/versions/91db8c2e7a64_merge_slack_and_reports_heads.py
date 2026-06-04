"""merge slack and reports heads

Revision ID: 91db8c2e7a64
Revises: 2e7e9301d754, 6c9f3a1b8d21
Create Date: 2026-06-03 15:40:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "91db8c2e7a64"
down_revision: Union[str, Sequence[str], None] = ("2e7e9301d754", "6c9f3a1b8d21")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
