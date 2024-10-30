"""add prize service tables

Revision ID: 885205739cb5
Revises: 6553307b1e33
Create Date: 2024-10-30 07:50:35.363190

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '885205739cb5'
down_revision = '6553307b1e33'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('raffles', 
        sa.Column('prize_pool_id', sa.Integer(), nullable=True)
    )
    op.add_column('raffles',
        sa.Column('draw_prize_count', sa.Integer(), nullable=True, server_default='0')
    )
    op.create_foreign_key(
        'fk_raffles_prize_pool_id', 'raffles',
        'prize_pools', ['prize_pool_id'], ['id']
    )

def downgrade():
    op.drop_constraint('fk_raffles_prize_pool_id', 'raffles', type_='foreignkey')
    op.drop_column('raffles', 'draw_prize_count')
    op.drop_column('raffles', 'prize_pool_id')