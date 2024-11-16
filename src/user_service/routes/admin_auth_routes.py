# src/user_service/routes/admin_auth_routes.py

from flask import Blueprint, request, jsonify
from src.shared.auth import token_required
from src.user_service.models.user import User
from src.user_service.services.admin_auth_service import AdminAuthService

admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/api/admin')

@admin_auth_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        result, error = AdminAuthService.authenticate_admin(
            username=username,
            password=password,
            request=request
        )

        if error:
            return jsonify({'error': error}), 401

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_admin():
    """Verify admin status"""
    try:
        # Get user from token_required decorator
        current_user = request.current_user
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
            
        if not current_user.is_admin:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Return user data with explicit admin status
        user_data = current_user.to_dict()
        user_data['isAdmin'] = current_user.is_admin
            
        return jsonify({'user': user_data}), 200
            
    except Exception as e:
        print(f"Verify error: {str(e)}")  # Add logging
        return jsonify({'error': 'Internal server error'}), 500