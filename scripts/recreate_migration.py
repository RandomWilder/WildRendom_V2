# scripts/recreate_migration.py
import logging
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
from alembic import op
import sqlalchemy as sa
from src.shared import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_base_migration():
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
            # Import ALL models to ensure proper registration
            from src.prize_service.models import Prize, PrizePool, PrizeAllocation
            from src.user_service.models import User, UserStatusChange, CreditTransaction
            from src.raffle_service.models import Raffle, Ticket
            from src.raffle_service.models import InstantWin, UserRaffleStats
            
            # Create the migration script
            from flask_migrate import migrate, init, stamp
            
            # Create initial migration with revision ID matching database
            migrate(
                message='recreate initial schema',
                rev_id='7fe6ec511f32'  # Use the existing version from database
            )
            
            logger.info("Successfully recreated base migration")
            return True
            
    except Exception as e:
        logger.error(f"Migration creation failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    create_base_migration()
    