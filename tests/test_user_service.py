import pytest
from flask import json
from datetime import datetime, UTC
from src.user_service import create_user_service
from src.shared import db
from src.user_service.models.user import User

@pytest.fixture
def auth_headers(client):
    """Create and log in a test user, return auth headers"""
    # Register user
    client.post('/api/users/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test123!@#'
    })
    
    # Login
    response = client.post('/api/users/login', json={
        'username': 'testuser',
        'password': 'Test123!@#'
    })
    
    token = json.loads(response.data)['token']
    return {'Authorization': f'Bearer {token}'}

def test_user_registration(client, init_database):
    """Test user registration endpoint"""
    response = client.post('/api/users/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test123!@#',
        'first_name': 'Test',
        'last_name': 'User'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['username'] == 'testuser'
    assert 'password' not in data
    assert data['email'] == 'test@example.com'

def test_duplicate_registration(client, init_database):
    """Test registration with existing username"""
    # First registration
    client.post('/api/users/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test123!@#'
    })
    
    # Duplicate registration
    response = client.post('/api/users/register', json={
        'username': 'testuser',
        'email': 'another@example.com',
        'password': 'Test123!@#'
    })
    
    assert response.status_code == 400
    assert b'Username already exists' in response.data

def test_user_login(client, init_database):
    """Test user login endpoint"""
    # Register user
    client.post('/api/users/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test123!@#'
    })
    
    # Login
    response = client.post('/api/users/login', json={
        'username': 'testuser',
        'password': 'Test123!@#'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert data['user']['username'] == 'testuser'

def test_invalid_login(client, init_database):
    """Test login with invalid credentials"""
    response = client.post('/api/users/login', json={
        'username': 'nonexistent',
        'password': 'wrong'
    })
    
    assert response.status_code == 401

def test_credit_management(client, init_database, auth_headers):
    """Test credit management endpoints"""
    # Register and login handled by auth_headers fixture
    
    # Get user ID
    response = client.get('/api/users/me', headers=auth_headers)
    user_id = json.loads(response.data)['id']
    
    # Add credits
    response = client.post(
        f'/api/users/credits/{user_id}',
        json={
            'amount': 100.0,
            'transaction_type': 'add'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['site_credits'] == 100.0
    
    # Subtract credits
    response = client.post(
        f'/api/users/credits/{user_id}',
        json={
            'amount': 30.0,
            'transaction_type': 'subtract'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['site_credits'] == 70.0

def test_insufficient_credits(client, init_database, auth_headers):
    """Test credit subtraction with insufficient balance"""
    # Get user ID
    response = client.get('/api/users/me', headers=auth_headers)
    user_id = json.loads(response.data)['id']
    
    # Attempt to subtract credits
    response = client.post(
        f'/api/users/credits/{user_id}',
        json={
            'amount': 100.0,
            'transaction_type': 'subtract'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert b'Insufficient credits' in response.data

def test_profile_update(client, init_database, auth_headers):
    """Test profile update endpoint"""
    # Get user ID
    response = client.get('/api/users/me', headers=auth_headers)
    user_id = json.loads(response.data)['id']
    
    # Update profile
    response = client.put(
        f'/api/users/profile/{user_id}',
        json={
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updated@example.com'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['first_name'] == 'Updated'
    assert data['last_name'] == 'User'
    assert data['email'] == 'updated@example.com'