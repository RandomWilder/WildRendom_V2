"""add prize service tables

Revision ID: 6553307b1e33
Revises: 9524cfd19850
Create Date: 2024-10-30 07:19:06.705301

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6553307b1e33'
down_revision = '9524cfd19850'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('prize_allocations', schema=None) as batch_op:
        batch_op.alter_column('allocation_config',
               existing_type=sa.TEXT(),
               type_=postgresql.JSON(astext_type=Text()),
               existing_nullable=True)

    with op.batch_alter_table('prize_pool_allocations', schema=None) as batch_op:
        batch_op.alter_column('allocation_rules',
               existing_type=sa.TEXT(),
               type_=postgresql.JSON(astext_type=Text()),
               existing_nullable=True)

    with op.batch_alter_table('prize_pools', schema=None) as batch_op:
        batch_op.alter_column('allocation_rules',
               existing_type=sa.TEXT(),
               type_=postgresql.JSON(astext_type=Text()),
               existing_nullable=True)
        batch_op.alter_column('win_limits',
               existing_type=sa.TEXT(),
               type_=postgresql.JSON(astext_type=Text()),
               existing_nullable=True)
        batch_op.alter_column('eligibility_rules',
               existing_type=sa.TEXT(),
               type_=postgresql.JSON(astext_type=Text()),
               existing_nullable=True)

    with op.batch_alter_table('prizes', schema=None) as batch_op:
        batch_op.alter_column('eligibility_rules',
               existing_type=sa.TEXT(),
               type_=postgresql.JSON(astext_type=Text()),
               existing_nullable=True)

    with op.batch_alter_table('raffles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prize_pool_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'prize_pools', ['prize_pool_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('raffles', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('prize_pool_id')

    with op.batch_alter_table('prizes', schema=None) as batch_op:
        batch_op.alter_column('eligibility_rules',
               existing_type=postgresql.JSON(astext_type=Text()),
               type_=sa.TEXT(),
               existing_nullable=True)

    with op.batch_alter_table('prize_pools', schema=None) as batch_op:
        batch_op.alter_column('eligibility_rules',
               existing_type=postgresql.JSON(astext_type=Text()),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('win_limits',
               existing_type=postgresql.JSON(astext_type=Text()),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('allocation_rules',
               existing_type=postgresql.JSON(astext_type=Text()),
               type_=sa.TEXT(),
               existing_nullable=True)

    with op.batch_alter_table('prize_pool_allocations', schema=None) as batch_op:
        batch_op.alter_column('allocation_rules',
               existing_type=postgresql.JSON(astext_type=Text()),
               type_=sa.TEXT(),
               existing_nullable=True)

    with op.batch_alter_table('prize_allocations', schema=None) as batch_op:
        batch_op.alter_column('allocation_config',
               existing_type=postgresql.JSON(astext_type=Text()),
               type_=sa.TEXT(),
               existing_nullable=True)

    # ### end Alembic commands ###
