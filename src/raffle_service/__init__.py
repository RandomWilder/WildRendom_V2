# src/raffle_service/__init__.py
from flask import Flask
from src.shared import db, migrate
from src.shared.config import config
from .routes.raffle_routes import raffle_bp
from .routes.admin_routes import admin_bp

def create_raffle_service(config_name='development'):
    """Create and configure the Raffle Service"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(raffle_bp, url_prefix='/api/raffles')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    return app