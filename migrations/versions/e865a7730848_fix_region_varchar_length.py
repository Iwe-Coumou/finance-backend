"""fix region varchar length

Revision ID: e865a7730848
Revises: ff1ae7e38be3
Create Date: 2026-03-13 17:36:19.938020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e865a7730848'
down_revision: Union[str, Sequence[str], None] = 'ff1ae7e38be3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('factor_returns', 'region',
                    type_=sa.String(),
                    postgresql_using='region::varchar')

def downgrade() -> None:
    op.alter_column('factor_returns', 'region',
                    type_=sa.String(length=3),
                    postgresql_using='region::varchar(3)')
