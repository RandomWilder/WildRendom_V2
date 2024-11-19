# scripts/init_migration.py
import logging
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
import sqlalchemy as sa
from src.shared import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_migration():
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
            # Import ALL models
            from src.prize_service.models import Prize, PrizePool, PrizeAllocation
            from src.user_service.models import User, UserStatusChange, CreditTransaction
            from src.raffle_service.models import Raffle, Ticket
            from src.raffle_service.models import InstantWin, UserRaffleStats
            
            # First, remove existing migration folder if it exists
            import shutil
            migration_path = project_root / 'migrations'
            if migration_path.exists():
                shutil.rmtree(migration_path)
            
            # Initialize new migrations
            from flask_migrate import init, migrate, stamp
            init()
            
            # Create initial migration with specific revision ID
            migrate(message='initial migration', rev_id='7fe6ec511f32')
            
            # Stamp the database with this revision
            stamp('7fe6ec511f32')
            
            logger.info("Successfully initialized migration state")
            return True
            
    except Exception as e:
        logger.error(f"Migration initialization failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    init_migration()