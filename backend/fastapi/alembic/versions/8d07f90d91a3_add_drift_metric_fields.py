"""add drift metric fields

Revision ID: 8d07f90d91a3
Revises: de420001643a
Create Date: 2026-05-06 14:03:39.695653
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8d07f90d91a3'
down_revision: Union[str, Sequence[str], None] = 'de420001643a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'drift_findings',
        sa.Column('psi_score', sa.Float(), nullable=True)
    )

    op.add_column(
        'drift_findings',
        sa.Column('ks_score', sa.Float(), nullable=True)
    )

    op.add_column(
        'drift_findings',
        sa.Column('ks_pvalue', sa.Float(), nullable=True)
    )

    op.add_column(
        'drift_findings',
        sa.Column('severity', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('drift_findings', 'severity')
    op.drop_column('drift_findings', 'ks_pvalue')
    op.drop_column('drift_findings', 'ks_score')
    op.drop_column('drift_findings', 'psi_score')