from flask import Flask, request
from flask_cors import CORS
from src.shared import db, migrate
from src.shared.config import config
from src.user_service.routes.user_routes import user_bp
from src.raffle_service.routes.raffle_routes import raffle_bp
from src.raffle_service.routes.admin_routes import raffle_admin_bp
from src.prize_service.routes.prize_routes import prize_bp
from src.prize_service.routes.admin_routes import admin_bp as prize_admin_bp

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Simplified CORS configuration
    CORS(app, 
         resources={r"/*": {
             "origins": ["http://localhost:5175"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Accept"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "send_wildcard": False
         }})
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(raffle_bp)
    app.register_blueprint(raffle_admin_bp)
    app.register_blueprint(prize_bp, url_prefix='/api/prizes')
    app.register_blueprint(prize_admin_bp, url_prefix='/api/admin/prizes')
    
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin == 'http://localhost:5175':
            response.headers.update({
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept',
                'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Type, Authorization'
            })
        return response
    
    return app

def run_app(host='0.0.0.0', port=5001):
    app = create_app()
    app.run(host=host, port=port)

if __name__ == "__main__":
    run_app()