from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from flask import Flask
from src.shared import db
from src.shared.config import config
from src.user_service.models.user import User

def verify_db():
    """Verify database setup"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    db.init_app(app)
    
    with app.app_context():
        # Check admin user
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Admin user found:")
            print(f"Username: {admin.username}")
            print(f"Email: {admin.email}")
            print(f"Is Admin: {admin.is_admin}")
            print(f"Is Active: {admin.is_active}")
        else:
            print("Admin user not found!")

if __name__ == "__main__":
    verify_db()