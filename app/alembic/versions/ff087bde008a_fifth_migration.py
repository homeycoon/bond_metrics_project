"""fifth migration

Revision ID: ff087bde008a
Revises: f6aa4cee3ad6
Create Date: 2024-10-12 00:16:18.095731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff087bde008a'
down_revision: Union[str, None] = 'f6aa4cee3ad6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('bonds', 'prev_close_price_cur',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=True)
    op.alter_column('bonds', 'prev_close_price_rub',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=True)
    op.alter_column('bonds', 'nominal_cur',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=True)
    op.alter_column('bonds', 'nominal_rub',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=True)
    op.alter_column('bonds', 'coupon_rate',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=True)
    op.alter_column('bonds', 'coupon_period',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('bonds', 'accum_coupon_cur',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=True)
    op.alter_column('bonds', 'accum_coupon_rub',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=True)
    op.alter_column('bonds', 'valuta_nominal',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('bonds', 'currency_curr',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('bonds', 'lot_size',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('bonds', 'issue_size',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('bonds', 'issue_size',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('bonds', 'lot_size',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('bonds', 'currency_curr',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('bonds', 'valuta_nominal',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('bonds', 'accum_coupon_rub',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=False)
    op.alter_column('bonds', 'accum_coupon_cur',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=False)
    op.alter_column('bonds', 'coupon_period',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('bonds', 'coupon_rate',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=False)
    op.alter_column('bonds', 'nominal_rub',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=False)
    op.alter_column('bonds', 'nominal_cur',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=False)
    op.alter_column('bonds', 'prev_close_price_rub',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=False)
    op.alter_column('bonds', 'prev_close_price_cur',
               existing_type=sa.NUMERIC(precision=20, scale=4),
               nullable=False)
    # ### end Alembic commands ###
