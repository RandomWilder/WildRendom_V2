# wsgi.py
from src.shared import db
from flask import Flask
from flask_migrate import Migrate
from src.shared.config import config

def create_app():
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    migrate = Migrate(app, db)
    return app

app = create_app()