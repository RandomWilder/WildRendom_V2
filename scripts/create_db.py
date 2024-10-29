# scripts/create_db.py
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from flask import Flask
from src.shared import db, migrate
from src.shared.config import config

def create_app():
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    return app

def init_db():
    """Initialize the database"""
    app = create_app()
    
    with app.app_context():
        # Import models here, after app context is established
        from src.user_service.models import User
        from src.raffle_service.models import Raffle, Ticket
        
        # Create database directory if it doesn't exist
        db_path = Path(app.config['PROJECT_ROOT']) / 'data'
        db_path.mkdir(exist_ok=True)
        
        try:
            print("Creating database tables...")
            db.create_all()
            
            print("Creating admin user...")
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    first_name='Admin',
                    last_name='User',
                    is_admin=True
                )
                admin_user.set_password('Admin123!@#')
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created successfully.")
            
            print("Database initialized successfully.")
            print(f"Database location: {db_path / 'wildrandom.db'}")
            
        except Exception as e:
            print(f"Error during database initialization: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    init_db()