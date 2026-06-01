"""restore missing revision placeholder

Revision ID: 2e7e9301d754
Revises: b771d77d183c
Create Date: 2026-06-01 11:45:00.000000

This revision restores a missing migration id that already exists in deployed
databases. It is intentionally a no-op so Alembic can traverse the history
chain safely and continue upgrading to later revisions.
"""

from typing import Sequence, Union


revision: str = "2e7e9301d754"
down_revision: Union[str, Sequence[str], None] = "b771d77d183c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
