# scripts/run_prize_migration.py

import os
import sys
from pathlib import Path
import logging
from flask import Flask
from flask_migrate import Migrate, init, upgrade
import alembic.command
from alembic.config import Config

# Fix path resolution
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
os.chdir(project_root)  # Change working directory to project root
sys.path.append(str(project_root))  # Add project root to Python path

from src.shared import db
from src.shared.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_migration():
    """Setup and run database migration"""
    try:
        # Import models to ensure they're registered
        from src.prize_service.models import Prize, PrizePool, PrizeAllocation
        from src.user_service.models import User
        from src.raffle_service.models import Raffle
        
        # Create Flask app with config
        app = Flask(__name__)
        app.config.from_object(config['development'])
        
        db.init_app(app)
        migration = Migrate(app, db)
        
        with app.app_context():
            # Create migrations directory if it doesn't exist
            migrations_dir = project_root / 'migrations'
            if not migrations_dir.exists():
                logger.info("Initializing migrations directory...")
                init(directory=str(migrations_dir))
            
            logger.info("Generating new migration...")
            alembic_cfg = Config(str(migrations_dir / "alembic.ini"))
            alembic_cfg.set_main_option("script_location", str(migrations_dir))
            alembic.command.revision(alembic_cfg, 
                                   message='prize service enhancement',
                                   autogenerate=True)
            
            logger.info("Applying migration...")
            alembic.command.upgrade(alembic_cfg, "head")
            
            logger.info("Migration completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    setup_migration()