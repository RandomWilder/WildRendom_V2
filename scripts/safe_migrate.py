# scripts/safe_migrate.py
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask
from flask_migrate import Migrate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_migration():
    """Create migration for ticket reservation tables"""
    try:
        # Setup Flask app and database
        app = Flask(__name__)
        project_root = Path(__file__).parent.parent
        app.config.update(
            SQLALCHEMY_DATABASE_URI=f'sqlite:///{project_root}/data/wildrandom.db',
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
        
        # Initialize database
        from src.shared import db
        db.init_app(app)
        
        # Setup migration
        migrate = Migrate(app, db)
        
        with app.app_context():
            # Import all models
            from src.prize_service.models import Prize, PrizePool, PrizeAllocation
            from src.user_service.models import User
            from src.raffle_service.models import Raffle, Ticket
            
            # Create migration
            from flask_migrate import migrate as create_migration
            
            # Generate migration file
            create_migration(message="add ticket reservation tables")
            logger.info("Created migration for ticket reservation tables")
            
            # Instructions for next steps
            logger.info("\nMigration created successfully!")
            logger.info("To apply the migration, run:")
            logger.info("flask db upgrade")
            
            return True
            
    except Exception as e:
        logger.error(f"Migration creation failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    create_migration()