from flask import Flask
from flask_migrate import Migrate
from src.shared import db
from src.shared.config import config

migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    return app