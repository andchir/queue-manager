"""Added queue table

Revision ID: d096b78093b0
Revises: d32b280f8ecd
Create Date: 2024-02-12 15:00:55.039422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd096b78093b0'
down_revision: Union[str, None] = 'd32b280f8ecd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('queue',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('uuid', sa.String(length=37), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('data', sa.String(length=256), nullable=False),
    sa.Column('owner', sa.String(length=256), nullable=False),
    sa.Column('time_created', sa.DateTime(timezone=True), nullable=False),
    sa.Column('time_updated', sa.DateTime(timezone=True), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('queue')
    # ### end Alembic commands ###