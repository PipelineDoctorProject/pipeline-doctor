"""fiels added in ml model"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "f4422db8b93f"
down_revision: Union[str, Sequence[str], None] = "ed8427f56e4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # add as nullable first
    op.add_column(
        "ml_models",
        sa.Column("tenant_id", sa.String(), nullable=True)
    )

    # optional:
    # set some default tenant id for old rows
    # op.execute(
    #     "UPDATE ml_models SET tenant_id='YOUR_TENANT_ID' WHERE tenant_id IS NULL"
    # )

    # create foreign key
    op.create_foreign_key(
        None,
        "ml_models",
        "tenants",
        ["tenant_id"],
        ["id"]
    )


def downgrade() -> None:

    op.drop_constraint(
        None,
        "ml_models",
        type_="foreignkey"
    )

    op.drop_column(
        "ml_models",
        "tenant_id"
    )