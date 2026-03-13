"""add region to factor_returns

Revision ID: e507b41117f8
Revises: 
Create Date: 2026-03-13 17:22:59.401440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e507b41117f8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('factor_returns', sa.Column('region', sa.String(length=3), nullable=True))
    op.execute("UPDATE factor_returns SET region = 'us' WHERE region IS NULL")
    op.drop_constraint('uq_factor_date_freq', 'factor_returns', type_='unique')
    op.create_unique_constraint('uq_factor_date_freq_region', 'factor_returns',
                                ['factor', 'date', 'frequency', 'region'])


def downgrade() -> None:
    op.drop_constraint('uq_factor_date_freq_region', 'factor_returns', type_='unique')
    op.create_unique_constraint('uq_factor_date_freq', 'factor_returns',
                                ['factor', 'date', 'frequency'])
    op.drop_column('factor_returns', 'region')
