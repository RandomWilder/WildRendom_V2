# src/user_service/routes/password_routes.py

from flask import Blueprint, request, jsonify
from src.shared.auth import token_required
from src.user_service.models.user import User
from src.user_service.services.password_service import PasswordService
from src.user_service.schemas.password_schema import (
    PasswordResetRequestSchema,
    PasswordResetSchema,
    PasswordChangeSchema
)
import logging

logger = logging.getLogger(__name__)
logger.info("Loading password_routes.py")

# Create blueprint with explicit url_prefix
password_bp = Blueprint('password', __name__, url_prefix='/api/users/password')
logger.info("Created password blueprint")

# Now routes are relative to /api/users/password
@password_bp.route('/test', methods=['GET'])
def test_password_routes():
    """Test route to verify password blueprint registration"""
    return jsonify({'message': 'Password routes working'}), 200


@password_bp.route('/reset-request', methods=['POST'])
def request_reset():
    """Request a password reset"""
    logger.debug("Reset request route accessed")
    try:
        schema = PasswordResetRequestSchema()
        data = schema.load(request.get_json())
        
        user = User.query.filter_by(email=data['email']).first()
        logger.debug(f"User lookup for {data['email']}: {'found' if user else 'not found'}")
        
        result, error = PasswordService.create_reset_request(
            email=data['email']
        )
        
        if error:
            logger.error(f"Reset request error: {error}")
            return jsonify({'error': error}), 400
            
        # The key fix - return the full result including the token
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in password reset request: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    

@password_bp.route('/reset', methods=['POST'])
def reset_password():
    """Reset password using token"""
    try:
        schema = PasswordResetSchema()
        data = schema.load(request.get_json())
        
        success, error = PasswordService.reset_password(
            token=data['token'],
            new_password=data['new_password']
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify({'message': 'Password reset successful'}), 200
        
    except Exception as e:
        logger.error(f"Error in password reset: {str(e)}")
        return jsonify({'error': str(e)}), 500

@password_bp.route('/change', methods=['PUT'])
@token_required
def change_password():
    """Change password for authenticated user"""
    try:
        schema = PasswordChangeSchema()
        data = schema.load(request.get_json())
        
        result, error = PasswordService.change_password(
            user_id=request.current_user.id,
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error in password change: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500