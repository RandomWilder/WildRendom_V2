# scripts/baseline_db.py
import logging
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate, init
from alembic.config import Config as AlembicConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_baseline():
    """Setup baseline migration for existing database"""
    try:
        # Set up paths
        project_root = Path(__file__).parent.parent
        migrations_dir = project_root / 'migrations'
        
        # Clean up existing migrations if any
        if migrations_dir.exists():
            import shutil
            shutil.rmtree(migrations_dir)
            logger.info("Cleaned up existing migrations directory")
        
        # Initialize Flask app
        app = Flask(__name__)
        app.config.update(
            SQLALCHEMY_DATABASE_URI=f'sqlite:///{project_root}/data/wildrandom.db',
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
        
        # Initialize database and migrate
        from src.shared import db
        db.init_app(app)
        Migrate(app, db)
        
        with app.app_context():
            # Initialize migrations directory
            init(directory=str(migrations_dir))
            logger.info("Initialized new migrations directory")
            
            # Create and configure alembic.ini
            config = AlembicConfig(str(migrations_dir / 'alembic.ini'))
            config.set_main_option('script_location', str(migrations_dir))
            
            # Import all models to ensure they're registered
            from src.prize_service.models import Prize, PrizePool, PrizeAllocation
            from src.user_service.models import User
            from src.raffle_service.models import Raffle, Ticket
            
            # Stamp current version
            from flask_migrate import stamp
            stamp(directory=str(migrations_dir))
            logger.info("Stamped database with baseline version")
            
            logger.info("\nBaseline setup complete!")
            logger.info("You can now create new migrations safely.")
            
            return True
            
    except Exception as e:
        logger.error(f"Baseline setup failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    setup_baseline()