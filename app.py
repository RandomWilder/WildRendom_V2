# app.py
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from typing import Optional
from src.shared import db, migrate
from src.shared.config import config
from src.user_service.routes.user_routes import user_bp
from src.raffle_service.routes.raffle_routes import raffle_bp
from src.raffle_service.routes.admin_routes import raffle_admin_bp
from src.prize_service.routes.prize_routes import prize_bp
from src.prize_service.routes.admin_routes import admin_bp as prize_admin_bp
from src.raffle_service.routes.reservation_routes import reservation_bp
from src.raffle_service.routes.payment_routes import payment_bp
from src.raffle_service.routes.ticket_routes import ticket_bp
from src.user_service.routes.admin_auth_routes import admin_auth_bp
from src.user_service.routes.tier_routes import tier_bp
from src.user_service.routes.password_routes import password_bp  # Add this import
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_name: str = 'development') -> Flask:
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure CORS with specific settings
    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": ["http://localhost:5175"],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "Accept"],
                 "expose_headers": ["Content-Type", "Authorization"],
                 "supports_credentials": True,
                 "send_wildcard": False
             }
         })
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints with explicit prefixes
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(raffle_bp, url_prefix='/api/raffles')
    app.register_blueprint(raffle_admin_bp, url_prefix='/api/admin/raffles')
    app.register_blueprint(prize_bp, url_prefix='/api/prizes')
    app.register_blueprint(prize_admin_bp, url_prefix='/api/admin/prizes')
    app.register_blueprint(reservation_bp, url_prefix='/api/reservations')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')
    app.register_blueprint(ticket_bp, url_prefix='/api/tickets')
    app.register_blueprint(admin_auth_bp, url_prefix='/api/admin')
    app.register_blueprint(tier_bp)
    app.register_blueprint(password_bp)  # Add this line
    
    # Add diagnostics logging for registered routes
    logger.info("\nRegistered Routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.rule}")
    
    return app

def run_app(host: str = '0.0.0.0', port: int = 5001) -> None:
    """Run the Flask application"""
    app = create_app()
    app.run(host=host, port=port, debug=True)

if __name__ == "__main__":
    run_app()