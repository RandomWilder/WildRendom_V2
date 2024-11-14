import sys
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db
from src.shared.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_migrations():
    """Initialize migrations with all models loaded."""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)

    with app.app_context():
        # Import ALL models here
        from src.user_service.models import User, UserStatusChange, CreditTransaction, UserActivity
        from src.prize_service.models import Prize, PrizePool, PrizeAllocation, PrizeInstance
        from src.raffle_service.models import Raffle, Ticket, InstantWin, RaffleStatusChange, UserRaffleStats
        from src.reservation_service.models.reservation import TicketReservation, ReservedTicket
        
        # Initialize migration
        from flask_migrate import Migrate
        migrate = Migrate(app, db)
        
        logger.info("All models loaded successfully")
        return app, migrate

if __name__ == "__main__":
    app, migrate = init_migrations()
    logger.info("Migration initialization ready. Now run:")
    logger.info("1. flask db init")
    logger.info("2. flask db migrate -m 'add reservation tables'")
    logger.info("3. After verifying migration file, run: flask db upgrade")