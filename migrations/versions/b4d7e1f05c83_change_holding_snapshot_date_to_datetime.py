"""change portfolio_holdings snapshot_date to datetime

Revision ID: b4d7e1f05c83
Revises: a1c3f8e92d47
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4d7e1f05c83'
down_revision: Union[str, Sequence[str], None] = 'a1c3f8e92d47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'portfolio_holdings',
        'snapshot_date',
        type_=sa.DateTime(),
        existing_type=sa.Date(),
        postgresql_using='snapshot_date::timestamp',
    )


def downgrade() -> None:
    op.alter_column(
        'portfolio_holdings',
        'snapshot_date',
        type_=sa.Date(),
        existing_type=sa.DateTime(),
        postgresql_using='snapshot_date::date',
    )
