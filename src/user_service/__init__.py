from flask import Flask
from src.shared import db, migrate
from src.shared.config import config
from src.user_service.routes.user_routes import user_bp

def create_user_service(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(user_bp, url_prefix='/api/users')
    
    return app