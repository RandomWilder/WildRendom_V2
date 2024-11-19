"""add user auth fields

Revision ID: f1a28cb257eb
Revises: 7fe6ec511f32
Create Date: 2024-11-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'f1a28cb257eb'
down_revision = '7fe6ec511f32'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('phone_number', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('auth_provider', sa.String(20), server_default='local'))
        batch_op.add_column(sa.Column('google_id', sa.String(100), nullable=True))

def downgrade():
    # Remove columns
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('google_id')
        batch_op.drop_column('auth_provider')
        batch_op.drop_column('phone_number')
