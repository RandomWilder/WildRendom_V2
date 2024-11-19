# scripts/fix_migrations.py
import logging
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
import sqlalchemy as sa
from sqlalchemy import text
from src.shared import db
import os

# Set up logging to be more verbose
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_migrations():
    logger.info("Starting migration fix process...")
    try:
        logger.info("Creating Flask app...")
        app = Flask(__name__)
        project_root = Path(__file__).parent.parent
        logger.info(f"Project root: {project_root}")
        
        # Check if database exists
        db_path = project_root / 'data' / 'wildrandom.db'
        logger.info(f"Checking database at: {db_path}")
        if not db_path.exists():
            logger.error(f"Database file not found at {db_path}")
            return False

        app.config.update(
            SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
        
        logger.info("Initializing database...")
        db.init_app(app)
        
        with app.app_context():
            logger.info("Checking current database version...")
            try:
                result = db.session.execute(text("SELECT version_num from alembic_version"))
                current_version = result.scalar()
                logger.info(f"Current database version: {current_version}")
            except Exception as e:
                logger.error(f"Error reading database version: {str(e)}")
                raise
            
            # Create migrations directory
            migrations_path = project_root / 'migrations'
            version_path = migrations_path / 'versions'
            logger.info(f"Creating migrations directories at: {migrations_path}")
            
            # Ensure directories exist
            migrations_path.mkdir(exist_ok=True)
            version_path.mkdir(exist_ok=True)
            
            # Create initial version file
            version_file = version_path / f'{current_version}_initial_schema.py'
            logger.info(f"Creating initial version file: {version_file}")
            
            with open(version_file, 'w') as f:
                f.write(f"""\"\"\"initial schema

Revision ID: {current_version}
Revises: 
Create Date: 2024-11-18 10:00:00.000000

\"\"\"
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '{current_version}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # This represents your current database state
    pass

def downgrade():
    pass
""")
            
            # Create new migration file
            import uuid
            new_version = uuid.uuid4().hex[:12]
            new_migration_file = version_path / f'{new_version}_add_user_auth_fields.py'
            logger.info(f"Creating new migration file: {new_migration_file}")
            
            with open(new_migration_file, 'w') as f:
                f.write(f"""\"\"\"add user auth fields

Revision ID: {new_version}
Revises: {current_version}
Create Date: 2024-11-18 10:00:00.000000

\"\"\"
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '{new_version}'
down_revision = '{current_version}'
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
""")
            
            logger.info("Migration files created successfully!")
            logger.info("Next steps:")
            logger.info("1. Review the migration files in migrations/versions/")
            logger.info("2. Run: flask db upgrade")
            
            return True
            
    except Exception as e:
        logger.error(f"Migration fix failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = fix_migrations()
    logger.info(f"Migration fix completed with status: {'Success' if success else 'Failed'}")