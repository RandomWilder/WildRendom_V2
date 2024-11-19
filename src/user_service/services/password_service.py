# src/user_service/services/password_service.py

from typing import Optional, Tuple, Dict
from datetime import datetime, timezone, timedelta
import secrets
from sqlalchemy.exc import SQLAlchemyError
from src.shared import db
from src.user_service.models.user import User
from src.user_service.models.password_reset import PasswordReset
from src.user_service.services.email_service import EmailService
from flask import current_app
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Force debug level for this file

# Add a handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

class PasswordService:
    
    TOKEN_LENGTH = 64  # Length of reset token
    TOKEN_EXPIRY_HOURS = 24  # Token validity period
    
    @staticmethod
    def create_reset_request(email: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Create password reset request"""
        try:
            logger.warning("Starting password reset request")  # Using WARNING to ensure visibility
            user = User.query.filter_by(email=email).first()
            
            if not user:
                logger.warning(f"No user found for email: {email}")
                return {'request_id': None}, None
                
            # Generate secure token
            token = secrets.token_urlsafe(PasswordService.TOKEN_LENGTH)
            logger.warning(f"IMPORTANT - Generated reset token: {token}")  # Using WARNING for token
            
            expires_at = datetime.now(timezone.utc) + timedelta(hours=PasswordService.TOKEN_EXPIRY_HOURS)
            
            # Create reset request
            reset_request = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            
            db.session.add(reset_request)
            db.session.commit()

            # Send email (placeholder for now)
            EmailService.send_password_reset_email(
                email=user.email,
                token=token,
                expiry=expires_at
            )
            
            logger.warning(f"Password reset request completed. Token: {token}")
            
            return {
                'message': 'If the email exists in our system, a reset link has been sent',
                'request_id': reset_request.id,
                'token': token,
            }, None
                
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in create_reset_request: {str(e)}")
            return None, "Failed to create reset request"

            
    @staticmethod
    def reset_password(token: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """Reset password using token"""
        try:
            # Find valid reset request
            reset_request = PasswordReset.query.filter(
                PasswordReset.token == token,
                PasswordReset.expires_at > datetime.now(timezone.utc),
                PasswordReset.used.is_(False)
            ).first()
            
            if not reset_request:
                return False, "Invalid or expired reset token"
                
            # Get user
            user = User.query.get(reset_request.user_id)
            if not user:
                return False, "User not found"
                
            # Update password
            user.set_password(new_password)
            reset_request.used = True
            reset_request.used_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            return True, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in reset_password: {str(e)}")
            return False, "Failed to reset password"
            
    @staticmethod
    def change_password(user_id: int, current_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """Change password for authenticated user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
                
            # Verify current password
            if not user.check_password(current_password):
                return False, "Current password is incorrect"
                
            # Update password
            user.set_password(new_password)
            db.session.commit()
            
            return True, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in change_password: {str(e)}")
            return False, "Failed to change password"