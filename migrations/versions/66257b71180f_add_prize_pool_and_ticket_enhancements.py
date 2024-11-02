"""Add missing prize pool and ticket columns

Revision ID: 66257b71180f
Revises: 
Create Date: 2024-10-31 01:41:45.712000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '66257b71180f'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Prize Pool Enhancements - only add missing columns
    with op.batch_alter_table('prize_pools') as batch_op:
        # Check existing columns showed these are missing
        batch_op.add_column(sa.Column('odds_configuration', sa.Text()))
        batch_op.add_column(sa.Column('total_prizes', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('available_prizes', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('total_value', sa.Numeric(10, 2), nullable=False, server_default='0'))

    # Ticket Enhancements - add new reveal mechanism columns
    with op.batch_alter_table('tickets') as batch_op:
        batch_op.add_column(sa.Column('is_revealed', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('reveal_time', sa.DateTime()))
        batch_op.add_column(sa.Column('reveal_sequence', sa.Integer()))
        batch_op.add_column(sa.Column('instant_win_eligible', sa.Boolean(), nullable=False, server_default='0'))
        
        # Add new index for reveal queries
        batch_op.create_index('idx_ticket_reveal', ['raffle_id', 'user_id', 'reveal_time'])

def downgrade():
    # Remove Ticket enhancements
    with op.batch_alter_table('tickets') as batch_op:
        batch_op.drop_index('idx_ticket_reveal')
        batch_op.drop_column('instant_win_eligible')
        batch_op.drop_column('reveal_sequence')
        batch_op.drop_column('reveal_time')
        batch_op.drop_column('is_revealed')

    # Remove Prize Pool enhancements
    with op.batch_alter_table('prize_pools') as batch_op:
        batch_op.drop_column('total_value')
        batch_op.drop_column('available_prizes')
        batch_op.drop_column('total_prizes')
        batch_op.drop_column('odds_configuration')