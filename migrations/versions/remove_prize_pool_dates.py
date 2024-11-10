"""remove date columns from prize pools

Revision ID: remove_prize_pool_dates
Revises: 
Create Date: 2024-11-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import logging

# revision identifiers, used by Alembic.
revision = 'remove_prize_pool_dates'
down_revision = None
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

def verify_table():
    """Verify prize_pools table exists and has expected columns"""
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'prize_pools' not in inspector.get_table_names():
        logger.error("prize_pools table not found!")
        return False
        
    columns = [col['name'] for col in inspector.get_columns('prize_pools')]
    required = ['start_date', 'end_date']
    
    if not all(col in columns for col in required):
        logger.error("Required columns not found in prize_pools!")
        return False
        
    return True

def backup_data():
    """Backup existing data"""
    conn = op.get_bind()
    result = conn.execute(text('SELECT id, start_date, end_date FROM prize_pools')).fetchall()
    return result

def upgrade():
    """Remove date columns from prize_pools"""
    # Safety checks
    if not verify_table():
        raise Exception("Safety check failed!")
    
    logger.info("Starting column removal...")
    try:
        with op.batch_alter_table('prize_pools', schema=None) as batch_op:
            batch_op.drop_column('start_date')
            batch_op.drop_column('end_date')
            
        logger.info("Successfully removed date columns")
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise

def downgrade():
    """Restore date columns if needed"""
    try:
        with op.batch_alter_table('prize_pools', schema=None) as batch_op:
            batch_op.add_column(sa.Column('start_date', sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column('end_date', sa.DateTime(), nullable=True))
            
        logger.info("Successfully restored date columns")
        
    except Exception as e:
        logger.error(f"Error during downgrade: {str(e)}")
        raise