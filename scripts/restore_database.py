# scripts/restore_database.py

from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared import db
from src.shared.config import config
from flask import Flask
from src.user_service.models import User
from src.prize_service.models import Prize, PrizePool, PrizeAllocation
from src.raffle_service.models import Raffle, Ticket, InstantWin, RaffleStatusChange
from src.user_service.models import UserActivity, UserStatusChange, CreditTransaction

def create_app():
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    return app

def recreate_database():
    """Recreate all database tables"""
    app = create_app()
    
    with app.app_context():
        print("Recreating database...")
        
        # Drop all existing tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("\nCreated tables:")
        # Print created tables for verification
        for table in db.metadata.tables:
            print(f"- {table}")
            
        print("\nDatabase recreation completed.")

if __name__ == "__main__":
    recreate_database()