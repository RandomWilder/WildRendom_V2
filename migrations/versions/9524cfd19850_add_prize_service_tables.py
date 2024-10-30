"""add prize service tables

Revision ID: 9524cfd19850
Revises: 
Create Date: 2024-10-29 19:50:03.434482

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql
import json

# revision identifiers, used by Alembic.
revision = '9524cfd19850'
down_revision = None
branch_labels = None
depends_on = None


# We'll use this to handle JSON in SQLite
class SQLiteJSON(sa.types.TypeDecorator):
    impl = sa.Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

def upgrade():
    # Create prizes table
    op.create_table('prizes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('custom_type', sa.String(length=50), nullable=True),
        sa.Column('tier', sa.String(length=20), nullable=False),
        sa.Column('tier_priority', sa.Integer(), nullable=True),
        sa.Column('retail_value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('cash_value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('credit_value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_quantity', sa.Integer(), nullable=True),
        sa.Column('available_quantity', sa.Integer(), nullable=True),
        sa.Column('min_threshold', sa.Integer(), nullable=True),
        sa.Column('total_won', sa.Integer(), nullable=True),
        sa.Column('total_claimed', sa.Integer(), nullable=True),
        sa.Column('win_limit_per_user', sa.Integer(), nullable=True),
        sa.Column('win_limit_period_days', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('eligibility_rules', SQLiteJSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create prize_pools table
    op.create_table('prize_pools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('allocation_strategy', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('budget_limit', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('current_allocation', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('allocation_rules', SQLiteJSON(), nullable=True),
        sa.Column('win_limits', SQLiteJSON(), nullable=True),
        sa.Column('eligibility_rules', SQLiteJSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create prize_pool_allocations table
    op.create_table('prize_pool_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pool_id', sa.Integer(), nullable=False),
        sa.Column('prize_id', sa.Integer(), nullable=False),
        sa.Column('quantity_allocated', sa.Integer(), nullable=False),
        sa.Column('quantity_remaining', sa.Integer(), nullable=False),
        sa.Column('allocation_rules', SQLiteJSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pool_id'], ['prize_pools.id'], ),
        sa.ForeignKeyConstraint(['prize_id'], ['prizes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create prize_allocations table
    op.create_table('prize_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prize_id', sa.Integer(), nullable=False),
        sa.Column('pool_id', sa.Integer(), nullable=False),
        sa.Column('allocation_type', sa.String(length=20), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('winner_user_id', sa.Integer(), nullable=True),
        sa.Column('won_at', sa.DateTime(), nullable=True),
        sa.Column('claim_status', sa.String(length=20), nullable=True),
        sa.Column('claim_deadline', sa.DateTime(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('claim_method', sa.String(length=20), nullable=True),
        sa.Column('value_claimed', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('allocation_config', SQLiteJSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['pool_id'], ['prize_pools.id'], ),
        sa.ForeignKeyConstraint(['prize_id'], ['prizes.id'], ),
        sa.ForeignKeyConstraint(['winner_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('prize_allocations')
    op.drop_table('prize_pool_allocations')
    op.drop_table('prize_pools')
    op.drop_table('prizes')