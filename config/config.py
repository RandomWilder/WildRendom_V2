# config/config.py
from typing import Dict, Type
import os
from pathlib import Path
from dataclasses import dataclass

@dataclass
class BaseConfig:
    # Base Configuration
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    APP_NAME: str = "WildRandom"
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{PROJECT_ROOT}/data/wildrandom.db'
    )
    
    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-key-please-change')
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'jwt-key-please-change')
    
    # Service Ports
    USER_SERVICE_PORT: int = 5001
    RAFFLE_SERVICE_PORT: int = 5002
    PRIZE_SERVICE_PORT: int = 5003
    PROMOTIONS_SERVICE_PORT: int = 5004
    ANALYSIS_SERVICE_PORT: int = 5005

@dataclass
class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    TESTING: bool = False

@dataclass
class TestingConfig(BaseConfig):
    DEBUG: bool = False
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'

@dataclass
class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    TESTING: bool = False
    
    def __post_init__(self):
        if not os.getenv('SECRET_KEY'):
            raise ValueError("SECRET_KEY must be set in production")
        if not os.getenv('JWT_SECRET_KEY'):
            raise ValueError("JWT_SECRET_KEY must be set in production")

# Config dictionary for easy access
config: Dict[str, Type[BaseConfig]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# src/shared/database.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# src/shared/logging_config.py
import logging
from pathlib import Path
from typing import Optional

def setup_logger(
    service_name: str,
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """Configure logging for a service"""
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# scripts/create_db.py
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.shared.database import db
from config.config import config

def init_db():
    """Initialize the database"""
    from flask import Flask
    
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    db.init_app(app)
    
    with app.app_context():
        # Create database directory if it doesn't exist
        db_path = Path(app.config['PROJECT_ROOT']) / 'data'
        db_path.mkdir(exist_ok=True)
        
        # Create all tables
        db.create_all()
        print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()

# requirements.txt
flask==3.0.3
flask-sqlalchemy==3.1.1
flask-migrate==4.0.7
flask-jwt-extended==4.6.0
python-dotenv==1.0.1
pytest==8.0.2
black==24.2.0
isort==5.13.2
flake8==7.0.0
mypy==1.8.0
pydantic==2.6.1
sqlalchemy==2.0.27
alembic==1.13.1
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.6