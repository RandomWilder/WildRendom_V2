# scripts/migrate_db.py
from pathlib import Path
import sys
import argparse
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db, migrate
from src.shared.config import config

# Import all models that need migration
from src.prize_service.models import Prize, PrizePool, PrizeAllocation
from src.raffle_service.models import Ticket, Raffle
from src.user_service.models import User

def init_migrations(app):
    """Initialize migrations directory if it doesn't exist"""
    migrations_dir = Path(project_root) / 'migrations'
    
    if not migrations_dir.exists():
        logging.info("Initializing migrations directory...")
        try:
            from flask_migrate import init as init_migrations
            with app.app_context():
                init_migrations('migrations')
            logging.info("Migrations directory initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing migrations: {e}")
            raise

def create_migration(app):
    """Generate new migration script"""
    logging.info("Generating new migration...")
    try:
        from flask_migrate import migrate
        
        with app.app_context():
            migrate(directory='migrations', message='Add prize pool and ticket enhancements')
        logging.info("Migration script generated successfully.")
    except Exception as e:
        logging.error(f"Error generating migration: {e}")
        raise

def apply_migration(app):
    """Apply pending migrations"""
    logging.info("Applying migrations...")
    try:
        from flask_migrate import upgrade
        
        with app.app_context():
            upgrade(directory='migrations')
        logging.info("Migrations applied successfully.")
    except Exception as e:
        logging.error(f"Error applying migrations: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Database migration management')
    parser.add_argument('action', choices=['init', 'generate', 'apply'],
                       help='Action to perform: initialize migrations, generate new migration, or apply migrations')
    
    args = parser.parse_args()
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    try:
        if args.action == 'init':
            init_migrations(app)
        elif args.action == 'generate':
            create_migration(app)
        elif args.action == 'apply':
            apply_migration(app)
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()