# migrations_app.py

from flask import Flask
from src.shared import db, migrate
from src.shared.config import config

# Import all models to ensure they're registered with SQLAlchemy
from src.prize_service.models import Prize, PrizePool, PrizeAllocation
from src.user_service.models import User
from src.raffle_service.models import Raffle, Ticket

def create_app():
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    return app

app = create_app()
