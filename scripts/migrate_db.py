# scripts/migrate_db.py
import os
import sys
from pathlib import Path
import shutil

# Fix path properly
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
os.chdir(project_root)
sys.path.append(str(project_root))

import logging
from flask import Flask
from flask_migrate import Migrate
import sqlalchemy as sa

from src.shared import db
from src.shared.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    db_path = project_root / 'data' / 'wildrandom.db'
    db_path.parent.mkdir(exist_ok=True)
    
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    db.init_app(app)
    return app

def reset_migration_state():
    """Reset migration state while preserving database"""
    # Remove migrations directory
    migrations_dir = project_root / 'migrations'
    if migrations_dir.exists():
        logger.info("Removing existing migrations directory...")
        shutil.rmtree(migrations_dir)
    
    # Clean alembic_version table
    app = create_app()
    with app.app_context():
        try:
            db.session.execute(sa.text('DROP TABLE IF EXISTS alembic_version;'))
            db.session.commit()
            logger.info("Reset migration state successfully")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting state: {e}")
            raise

def init_migrations():
    """Initialize fresh migration state"""
    app = create_app()
    migrate = Migrate(app, db)
    
    with app.app_context():
        # Import all models
        from src.prize_service.models import Prize
        from src.user_service.models import User
        from src.raffle_service.models import Raffle
        
        migrate.init_app(app, db)
        logger.info("Migrations initialized")

if __name__ == "__main__":
    try:
        logger.info("Starting migration reset process...")
        reset_migration_state()
        
        logger.info("Initializing new migration...")
        init_migrations()
        
        logger.info("Migration setup complete! Now you can run: flask db migrate")
        
    except Exception as e:
        logger.error(f"Error during migration setup: {e}")
        raise