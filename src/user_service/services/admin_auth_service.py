# src/user_service/services/admin_auth_service.py

from typing import Optional, Tuple, Dict
from datetime import datetime, timezone
from src.shared import db
from src.user_service.models.user import User
from src.user_service.models.user_activity import UserActivity
from flask import Request
from src.shared.auth import create_token

class AdminAuthService:
    @staticmethod
    def authenticate_admin(username: str, password: str, request: Request) -> Tuple[Optional[Dict], Optional[str]]:
        """Authenticate an admin user"""
        try:
            # Debug log
            print(f"Attempting admin authentication for user: {username}")
            
            user = User.query.filter_by(username=username).first()
            
            if not user:
                return None, "Invalid admin credentials"

            if not user.check_password(password):
                return None, "Invalid admin credentials"

            # Debug log
            print(f"User found, is_admin: {user.is_admin}")
            
            if not user.is_admin:
                return None, "Unauthorized: Admin access required"

            if not user.is_active:
                return None, "Account is deactivated"

            # Create auth token with admin flag
            token_data = {
                'user_id': user.id,
                'is_admin': True  # Include admin flag in token
            }
            token = create_token(user.id, additional_data=token_data)

            # Log admin login activity
            activity = UserActivity(
                user_id=user.id,
                activity_type='admin_login',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                status='success'
            )
            
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            
            db.session.add(activity)
            db.session.commit()

            user_data = user.to_dict()
            user_data['is_admin'] = True  # Ensure is_admin is explicitly set

            return {
                'user': user_data,
                'token': token
            }, None

        except Exception as e:
            print(f"Admin authentication error: {str(e)}")  # Debug log
            db.session.rollback()
            return None, str(e)
        
class AdminAuthService:
    @staticmethod
    def authenticate_admin(username: str, password: str, request: Request) -> Tuple[Optional[Dict], Optional[str]]:
        """Authenticate an admin user"""
        try:
            user = User.query.filter_by(username=username).first()
            
            if not user or not user.check_password(password):
                return None, "Invalid admin credentials"

            if not user.is_admin:
                return None, "Unauthorized: Admin access required"

            if not user.is_active:
                return None, "Account is deactivated"

            # Create standard token
            token = create_token(user.id)

            # Include admin status in response
            user_data = user.to_dict()
            user_data['isAdmin'] = user.is_admin

            return {
                'user': user_data,
                'token': token
            }, None

        except Exception as e:
            print(f"Admin authentication error: {str(e)}")
            return None, str(e)