#scripts/migrate_db.py
from pathlib import Path
import sys
import argparse
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db, migrate as flask_migrate  # Renamed the import
from src.shared.config import config
from src.user_service.models.user import User
from src.raffle_service.models import InstantWin
# Add these imports
from src.prize_service.models import Prize, PrizePool, PrizeAllocation, PrizePoolAllocation
from src.prize_service.models.prize import PrizeType, PrizeStatus, PrizeTier

def init_migrations(app):
    """Initialize migrations directory if it doesn't exist"""
    migrations_dir = Path(project_root) / 'migrations'
    
    if not migrations_dir.exists():
        print("Initializing migrations directory...")
        from flask_migrate import init as init_migrations
        with app.app_context():
            init_migrations('migrations')
        print("Migrations directory initialized.")

def run_migrations(generate=False):
    """Run database migrations"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    # Initialize database and migrations
    db.init_app(app)
    flask_migrate.init_app(app, db)
    
    # Ensure migrations directory exists
    init_migrations(app)
    
    with app.app_context():
        try:
            if generate:
                print("Generating migration for model changes...")
                from flask_migrate import migrate, stamp
                
                # Create an initial migration
                migrate(directory='migrations', message='add prize service tables')
                
                # Get the database synchronized with the first migration
                stamp(directory='migrations', revision='head')
                
                print("Migration file generated. Check migrations/versions/ directory.")
            else:
                print("Running database migrations...")
                from flask_migrate import upgrade
                upgrade(directory='migrations')
                print("Migrations completed successfully.")
            
        except Exception as e:
            print(f"Error during migrations: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Database migration script')
    parser.add_argument('--generate', action='store_true', 
                      help='Generate migration file for model changes')
    args = parser.parse_args()
    
    run_migrations(generate=args.generate)