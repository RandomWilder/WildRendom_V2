# src/__init__.py

from flask import Flask
from flask_migrate import Migrate
from src.shared import db
from src.shared.config import config
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from src.user_service.routes.user_routes import user_bp
    from src.user_service.routes.admin_auth_routes import admin_auth_bp
    from src.user_service.routes.tier_routes import tier_bp
    from src.user_service.routes.password_routes import password_bp
    
    logger.debug("Registering blueprints...")
    
    # Register blueprints - note we don't add prefixes here since they're in the blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(tier_bp)
    app.register_blueprint(password_bp)
    
    logger.debug("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.debug(f"{rule.endpoint}: {rule}")
    
    return app