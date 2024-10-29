import os
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app
from src.shared import db

def run_service():
    """Run the Service"""
    # Get configuration from environment or use default
    config_name = os.getenv('FLASK_CONFIG', 'development')
    
    # Create and configure the app
    app = create_app(config_name)
    
    # Ensure database exists
    with app.app_context():
        db_path = Path(app.config['PROJECT_ROOT']) / 'data'
        db_path.mkdir(exist_ok=True)
        
        # Create tables if they don't exist
        try:
            db.create_all()
            print(f"Database initialized at: {db_path / 'wildrandom.db'}")
        except Exception as e:
            print(f"Error initializing database: {e}")
            print("Running database initialization script...")
            from scripts.create_db import init_db
            init_db()
    
    port = app.config.get('APP_PORT', 5001)
    
    print(f"Starting Service on port {port}")
    print(f"Configuration: {config_name}")
    
    # Run the application
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    run_service()