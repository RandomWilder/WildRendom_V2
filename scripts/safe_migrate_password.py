# scripts/safe_migrate_password.py
import logging
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
from alembic import op
import sqlalchemy as sa
from src.shared import db
from datetime import datetime
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_migration():
    """Create migration for password resets safely"""
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
            # Get database connection
            conn = db.session.connection()
            
            logger.info("Starting database update for password resets...")
            
            # Create password_resets table
            create_password_resets_table = text("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INTEGER NOT NULL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token VARCHAR(128) NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN DEFAULT 0,
                    used_at DATETIME,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            conn.execute(create_password_resets_table)
            logger.info("Created password_resets table")

            # Create indexes
            create_indexes = [
                text("CREATE INDEX IF NOT EXISTS ix_password_resets_user_id ON password_resets (user_id)"),
                text("CREATE INDEX IF NOT EXISTS ix_password_resets_token ON password_resets (token)"),
                text("CREATE INDEX IF NOT EXISTS ix_password_resets_expires_at ON password_resets (expires_at)")
            ]
            for index_query in create_indexes:
                conn.execute(index_query)
            logger.info("Created indexes for password_resets")

            # Commit the transaction
            db.session.commit()
            logger.info("Successfully completed database update for password resets")
            
            return True

    except Exception as e:
        logger.error(f"Database update failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return False

if __name__ == "__main__":
    create_migration()