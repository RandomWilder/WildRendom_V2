import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional

class RaffleConfig:
    """Configuration settings for raffles"""
    # Transaction limits
    MAX_TICKETS_PER_TRANSACTION = 100
    MIN_TICKETS_PER_PURCHASE = 1
    
    # Time settings (in minutes)
    MIN_RAFFLE_DURATION = 30
    MAX_RAFFLE_DURATION = 1440  # 24 hours
    
    # Price settings
    MIN_TICKET_PRICE = 1.0
    MAX_TICKET_PRICE = 1000.0

    @staticmethod
    def validate_raffle_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate raffle creation/update parameters"""
        if 'ticket_price' in params:
            if not (RaffleConfig.MIN_TICKET_PRICE <= params['ticket_price'] <= RaffleConfig.MAX_TICKET_PRICE):
                return False, f"Ticket price must be between {RaffleConfig.MIN_TICKET_PRICE} and {RaffleConfig.MAX_TICKET_PRICE}"
        
        if 'total_tickets' in params:
            if params['total_tickets'] < 1:
                return False, "Total tickets must be at least 1"
                
        if 'max_tickets_per_user' in params:
            if params['max_tickets_per_user'] < 1:
                return False, "Maximum tickets per user must be at least 1"
                
        return True, None

class Config:
    # Base Configuration
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    APP_NAME = "WildRandom"
    APP_PORT = int(os.getenv('APP_PORT', 5001))  # Default port for all environments
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_PATH = PROJECT_ROOT / 'data' / 'wildrandom.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-please-change')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-key-please-change')

    # Raffle Configuration
    RAFFLE = RaffleConfig()

    @staticmethod
    def init_app(app):
        # Ensure data directory exists
        data_dir = Path(app.config['PROJECT_ROOT']) / 'data'
        data_dir.mkdir(exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}