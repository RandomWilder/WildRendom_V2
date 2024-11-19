# src/user_service/__init__.py

from flask import Flask
from src.shared import db, migrate
from src.shared.config import config
from src.user_service.routes.user_routes import user_bp
from src.user_service.routes.admin_auth_routes import admin_auth_bp
from src.user_service.routes.tier_routes import tier_bp
from src.user_service.routes.password_routes import password_bp
import logging

logger = logging.getLogger(__name__)

def create_user_service(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    logger.debug("Registering user service blueprints...")
    
    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(tier_bp)
    app.register_blueprint(password_bp)
    
    logger.debug("Registered user service routes:")
    for rule in app.url_map.iter_rules():
        logger.debug(f"{rule.endpoint}: {rule}")
    
    return app