# scripts/create_reservation_migration.py
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask
from flask_migrate import Migrate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_migration():
    """Create migration for ticket reservation tables"""
    try:
        # Setup Flask app
        app = Flask(__name__)
        project_root = Path(__file__).parent.parent
        app.config.update(
            SQLALCHEMY_DATABASE_URI=f'sqlite:///{project_root}/data/wildrandom.db',
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
        
        # Initialize database
        from src.shared import db
        db.init_app(app)
        migrate = Migrate(app, db)
        
        with app.app_context():
            # Import models including new reservation models
            from src.raffle_service.models import (
                Raffle, Ticket, InstantWin, UserRaffleStats,
                RaffleStatusChange, TicketReservation, ReservedTicket
            )
            from src.prize_service.models import Prize, PrizePool, PrizeAllocation
            from src.user_service.models import User
            
            # Create migration with new models
            from flask_migrate import revision
            revision(autogenerate=True, message="add ticket reservation tables")
            
            logger.info("Created migration for ticket reservation tables")
            logger.info("\nTo apply the migration, run:")
            logger.info("flask db upgrade")
            
            return True
            
    except Exception as e:
        logger.error(f"Migration creation failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    create_migration()