# scripts/stamp_db.py
import logging
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate, stamp, current
from src.shared import db
from alembic.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def stamp_database():
    """Stamp the database with the current migration version"""
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
            # Import models to ensure they're registered
            from src.prize_service.models import Prize, PrizePool, PrizeAllocation
            from src.user_service.models import User, UserStatusChange, CreditTransaction
            from src.raffle_service.models import Raffle, Ticket
            from src.raffle_service.models import InstantWin, UserRaffleStats
            
            # Get current revision before stamping
            current_rev = current()
            if current_rev:
                logger.info(f"Current database revision: {current_rev}")
                # Stamp with current revision instead of 'head'
                stamp(revision=current_rev)
                logger.info(f"Successfully stamped database with revision {current_rev}")
            else:
                logger.info("No current revision found. Initializing migrations...")
                # Initialize migrations if they don't exist
                from flask_migrate import init
                migrations_dir = project_root / 'migrations'
                if not migrations_dir.exists():
                    init()
                    logger.info("Initialized new migrations directory")
                
                # Now stamp with current heads
                stamp()
                logger.info("Successfully stamped database with initial revision")
                
            return True
            
    except Exception as e:
        logger.error(f"Error stamping database: {str(e)}")
        return False

if __name__ == "__main__":
    stamp_database()