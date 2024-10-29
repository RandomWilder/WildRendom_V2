# app.py

import os
from flask import Flask
from src.shared import db, migrate
from src.shared.config import config
from src.user_service.routes.user_routes import user_bp
from src.raffle_service.routes.raffle_routes import raffle_bp
from src.raffle_service.routes.admin_routes import admin_bp
from src.prize_service.routes.prize_routes import prize_bp
from src.prize_service.routes.admin_routes import admin_bp as prize_admin_bp

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(raffle_bp)  # raffle_bp already has url_prefix='/api/raffles'
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(prize_bp)  # Already has url_prefix='/api/prizes'
    app.register_blueprint(prize_admin_bp)  # Already has url_prefix='/api/admin/prizes'
    
    return app

def run_app(host='0.0.0.0', port=5001):
    """Run the application - called by start_system.py"""
    app = create_app()
    app.run(host=host, port=port)

if __name__ == "__main__":
    port = int(os.getenv('APP_PORT', 5001))
    run_app(port=port)