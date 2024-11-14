import os
import sys
from pathlib import Path
import shutil
import logging
from typing import Optional

# Fix path properly
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
os.chdir(project_root)
sys.path.append(str(project_root))

# After path setup, import Flask-related modules
try:
    from flask import Flask
    from flask_migrate import Migrate
    from sqlalchemy import text
    from src.shared import db
    from src.shared.config import config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all required packages are installed:")
    print("pip install flask flask-migrate sqlalchemy")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    db_path = project_root / 'data' / 'wildrandom.db'
    db_path.parent.mkdir(exist_ok=True)
    
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    db.init_app(app)
    return app

def reset_migration_state() -> Optional[str]:
    """Reset migration state while preserving database."""
    try:
        # Remove migrations directory
        migrations_dir = project_root / 'migrations'
        if migrations_dir.exists():
            logger.info("Removing existing migrations directory...")
            shutil.rmtree(migrations_dir)
        
        # Clean alembic_version table
        app = create_app()
        with app.app_context():
            db.session.execute(text('DROP TABLE IF EXISTS alembic_version;'))
            db.session.commit()
            logger.info("Reset migration state successfully")
            return None
    except Exception as e:
        error_msg = f"Error resetting migration state: {e}"
        logger.error(error_msg)
        return error_msg

def init_migrations() -> Optional[str]:
    """Initialize fresh migration state."""
    try:
        app = create_app()
        migrate = Migrate(app, db)
        
        with app.app_context():
            # Import all models
            from src.prize_service.models import Prize
            from src.user_service.models import User
            from src.raffle_service.models import Raffle
            from src.reservation_service.models.reservation import TicketReservation, ReservedTicket
            
            migrate.init_app(app, db)
            logger.info("Migrations initialized")
            return None
    except Exception as e:
        error_msg = f"Error initializing migrations: {e}"
        logger.error(error_msg)
        return error_msg

def main() -> None:
    """Main execution function."""
    logger.info("Starting migration reset process...")
    
    if error := reset_migration_state():
        sys.exit(1)
    
    logger.info("Initializing new migration...")
    if error := init_migrations():
        sys.exit(1)
    
    logger.info("Migration setup complete! Now run:")
    logger.info("1. flask db migrate -m 'add reservation tables'")
    logger.info("2. flask db upgrade")

if __name__ == "__main__":
    main()