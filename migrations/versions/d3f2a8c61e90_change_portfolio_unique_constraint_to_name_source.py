"""change portfolio unique constraint from name to name+source

Revision ID: d3f2a8c61e90
Revises: b4d7e1f05c83
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd3f2a8c61e90'
down_revision: Union[str, Sequence[str], None] = 'b4d7e1f05c83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('uq_portfolio_name', 'portfolios', type_='unique')
    op.create_unique_constraint('uq_portfolio_name_source', 'portfolios', ['name', 'source'])


def downgrade() -> None:
    op.drop_constraint('uq_portfolio_name_source', 'portfolios', type_='unique')
    op.create_unique_constraint('uq_portfolio_name', 'portfolios', ['name'])
