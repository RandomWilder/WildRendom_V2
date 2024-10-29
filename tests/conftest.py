import pytest
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.user_service import create_user_service
from src.shared import db

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_user_service('testing')
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def init_database(app):
    """Initialize test database"""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()