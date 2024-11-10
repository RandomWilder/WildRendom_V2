# scripts/create_raffle_migration.py

from pathlib import Path
import sys
import logging
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db, migrate
from src.shared.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_migration():
    """Create and run raffle schema migration"""
    try:
        app = Flask(__name__)
        app.config.from_object(config['development'])
        
        # Initialize extensions
        db.init_app(app)
        migrate.init_app(app, db)
        
        with app.app_context():
            # Import models to ensure they're registered with SQLAlchemy
            from src.raffle_service.models import Raffle
            from src.prize_service.models import PrizePool
            
            # Generate migration
            from flask_migrate import migrate as flask_migrate
            flask_migrate(message='raffle schema enhancement')
            
            logger.info("Raffle schema migration generated successfully")
            
    except Exception as e:
        logger.error(f"Migration generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    create_migration()