# scripts/clear_migration_state.py
import sys
from pathlib import Path
from sqlalchemy import text, inspect
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db
from src.shared.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_migration_state():
    """Clear migration version from database"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)

    with app.app_context():
        try:
            # Check if alembic_version table exists
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'alembic_version' in tables:
                db.session.execute(text('DELETE FROM alembic_version'))
                db.session.commit()
                logger.info("Successfully cleared migration state")
            else:
                logger.info("No migration state found - database is clean")
            
            # Verify database path
            db_path = Path(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            logger.info(f"Database location: {db_path}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during migration state check: {str(e)}")
            return False

if __name__ == "__main__":
    clear_migration_state()