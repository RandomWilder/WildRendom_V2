"""raffle schema enhancement

Revision ID: 2f46973c6ebf
Revises: remove_prize_pool_dates
Create Date: 2024-11-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2f46973c6ebf'
down_revision = 'remove_prize_pool_dates'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns first
    with op.batch_alter_table('raffles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prize_pool_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('draw_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('draw_distribution_type', sa.String(length=20), nullable=True))
        
        # Create foreign key with explicit name
        batch_op.create_foreign_key(
            'fk_raffle_prize_pool_id',  # Explicit constraint name
            'prize_pools',
            ['prize_pool_id'], ['id']
        )
        
        # Remove old columns
        batch_op.drop_column('instant_win_count')
        batch_op.drop_column('prize_structure')
        batch_op.drop_column('total_prize_count')

def downgrade():
    # Revert changes in reverse order
    with op.batch_alter_table('raffles', schema=None) as batch_op:
        # Add back old columns
        batch_op.add_column(sa.Column('total_prize_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('prize_structure', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('instant_win_count', sa.Integer(), nullable=True))
        
        # Remove new columns and constraints
        batch_op.drop_constraint('fk_raffle_prize_pool_id', type_='foreignkey')
        batch_op.drop_column('draw_distribution_type')
        batch_op.drop_column('draw_count')
        batch_op.drop_column('prize_pool_id')