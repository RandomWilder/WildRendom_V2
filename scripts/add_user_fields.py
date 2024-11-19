# scripts/add_user_fields.py
import logging
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
import sqlalchemy as sa
from src.shared import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_user_fields():
    try:
        app = Flask(__name__)
        project_root = Path(__file__).parent.parent
        app.config.update(
            SQLALCHEMY_DATABASE_URI=f'sqlite:///{project_root}/data/wildrandom.db',
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
        
        db.init_app(app)
        migrate = Migrate(app, db)
        
        with app.app_context():
            # Import models
            from src.user_service.models import User
            
            # Create new migration
            from flask_migrate import migrate
            
            # Add new columns migration
            with open(project_root / 'scripts' / 'migration_template.py', 'w') as f:
                f.write("""
def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('phone_number', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('auth_provider', sa.String(20), server_default='local'))
        batch_op.add_column(sa.Column('google_id', sa.String(100), nullable=True))

def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('google_id')
        batch_op.drop_column('auth_provider')
        batch_op.drop_column('phone_number')
""")
            
            # Create the migration
            migrate(message='add user auth fields', template=str(project_root / 'scripts' / 'migration_template.py'))
            
            logger.info("Successfully created migration for new user fields")
            return True
            
    except Exception as e:
        logger.error(f"Migration creation failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    add_user_fields()