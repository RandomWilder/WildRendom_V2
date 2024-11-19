# scripts/safe_migrate.py
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
    """Create migration for user tiers safely"""
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
            
            logger.info("Starting database update for user tiers...")
            
            # Create user_tiers table
            create_tiers_table = text("""
                CREATE TABLE IF NOT EXISTS user_tiers (
                    id INTEGER NOT NULL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    current_tier VARCHAR(20) NOT NULL DEFAULT 'bronze',
                    total_spent FLOAT DEFAULT 0.0,
                    total_participations INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0,
                    spend_90d FLOAT DEFAULT 0.0,
                    participations_90d INTEGER DEFAULT 0,
                    wins_90d INTEGER DEFAULT 0,
                    tier_updated_at DATETIME NOT NULL,
                    last_activity_date DATETIME NOT NULL,
                    purchase_limit_multiplier FLOAT DEFAULT 1.0,
                    early_access_hours INTEGER DEFAULT 0,
                    has_exclusive_access BOOLEAN DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            conn.execute(create_tiers_table)
            logger.info("Created user_tiers table")

            # Create user_tier_history table
            create_history_table = text("""
                CREATE TABLE IF NOT EXISTS user_tier_history (
                    id INTEGER NOT NULL PRIMARY KEY,
                    user_tier_id INTEGER NOT NULL,
                    previous_tier VARCHAR(20) NOT NULL,
                    new_tier VARCHAR(20) NOT NULL,
                    changed_at DATETIME NOT NULL,
                    FOREIGN KEY(user_tier_id) REFERENCES user_tiers(id)
                )
            """)
            conn.execute(create_history_table)
            logger.info("Created user_tier_history table")

            # Create indexes
            create_indexes = [
                text("CREATE INDEX IF NOT EXISTS ix_user_tiers_user_id ON user_tiers (user_id)"),
                text("CREATE INDEX IF NOT EXISTS ix_user_tiers_current_tier ON user_tiers (current_tier)"),
                text("CREATE INDEX IF NOT EXISTS ix_user_tier_history_user_tier_id ON user_tier_history (user_tier_id)")
            ]
            for index_query in create_indexes:
                conn.execute(index_query)
            logger.info("Created indexes")

            # Initialize tiers for existing users
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            init_tiers = text(f"""
                INSERT INTO user_tiers (
                    user_id, 
                    current_tier, 
                    tier_updated_at, 
                    last_activity_date
                )
                SELECT 
                    id, 
                    'bronze',
                    '{current_time}',
                    '{current_time}'
                FROM users 
                WHERE id NOT IN (SELECT user_id FROM user_tiers)
            """)
            conn.execute(init_tiers)
            logger.info("Initialized tiers for existing users")

            # Commit the transaction
            db.session.commit()
            logger.info("Successfully completed database update for user tiers")
            
            return True

    except Exception as e:
        logger.error(f"Database update failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return False

if __name__ == "__main__":
    create_migration()