# src/shared/auth.py

from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta, UTC
from src.shared import db

def create_token(user_id: int) -> str:
    """Create a JWT token for the user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.now(UTC) + timedelta(days=1),
        'iat': datetime.now(UTC)
    }
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def get_current_user():
    """Helper function to get current user from database"""
    # Import here to avoid circular import
    from src.user_service.models import User
    from src.user_service.services.activity_service import ActivityService
    
    token = request.headers.get('Authorization')
    
    if not token:
        ActivityService.log_activity(
            user_id=None,
            activity_type='auth_error',
            request=request,
            status='failed',
            details={'error': 'Token missing'}
        )
        return None, ('Token is missing', 401)
    
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        
        data = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        
        current_user = db.session.get(User, data['user_id'])
        if not current_user:
            ActivityService.log_activity(
                user_id=data.get('user_id'),
                activity_type='auth_error',
                request=request,
                status='failed',
                details={'error': 'Invalid user'}
            )
            return None, ('Invalid user', 401)
        
        return current_user, None
        
    except jwt.ExpiredSignatureError:
        ActivityService.log_activity(
            user_id=None,
            activity_type='auth_error',
            request=request,
            status='failed',
            details={'error': 'Token expired'}
        )
        return None, ('Token has expired', 401)
    except jwt.InvalidTokenError:
        ActivityService.log_activity(
            user_id=None,
            activity_type='auth_error',
            request=request,
            status='failed',
            details={'error': 'Invalid token'}
        )
        return None, ('Invalid token', 401)

def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user, error = get_current_user()
        if error:
            return jsonify({'error': error[0]}), error[1]
        
        request.current_user = current_user
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user, error = get_current_user()
        if error:
            return jsonify({'error': error[0]}), error[1]
        
        if not current_user.is_admin:
            from src.user_service.services.activity_service import ActivityService
            ActivityService.log_activity(
                user_id=current_user.id,
                activity_type='admin_access_error',
                request=request,
                status='failed',
                details={'error': 'Admin privileges required'}
            )
            return jsonify({'error': 'Admin privileges required'}), 403
        
        request.current_user = current_user
        return f(*args, **kwargs)
    return decorated