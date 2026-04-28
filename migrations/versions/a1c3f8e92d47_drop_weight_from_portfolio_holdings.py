"""drop weight from portfolio_holdings

Revision ID: a1c3f8e92d47
Revises: eb880e3db5c0
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c3f8e92d47'
down_revision: Union[str, Sequence[str], None] = 'eb880e3db5c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('portfolio_holdings', 'weight')


def downgrade() -> None:
    op.add_column('portfolio_holdings', sa.Column('weight', sa.Float(), nullable=False, server_default='0.0'))
    op.alter_column('portfolio_holdings', 'weight', server_default=None)
