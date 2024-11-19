from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from src.shared import db
from src.user_service.models import User, UserStatusChange, CreditTransaction
from flask import request
from src.user_service.services.activity_service import ActivityService
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Tuple[Optional[User], Optional[str]]:
        """Create a new user"""
        try:
            # Check for existing username
            if User.query.filter_by(username=user_data['username']).first():
                return None, "Username already exists"
            
            # Check for existing email
            if User.query.filter_by(email=user_data['email']).first():
                return None, "Email already exists"
            
            # Check for existing phone number if provided
            if user_data.get('phone_number') and User.query.filter_by(phone_number=user_data['phone_number']).first():
                return None, "Phone number already registered"
            
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                phone_number=user_data.get('phone_number'),
                auth_provider=user_data.get('auth_provider', 'local')
            )

            if user_data.get('auth_provider') == 'local':
                user.set_password(user_data['password'])
            elif user_data.get('auth_provider') == 'google':
                user.is_verified = True
            
            db.session.add(user)
            db.session.commit()

            logger.info(f"Created user: {user.username} with phone: {user.phone_number}")
            
            return user, None
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            return None, str(e)

    @staticmethod
    def authenticate_user(username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate a user"""
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                return None, "Invalid username or password"
            
            if not user.check_password(password):
                ActivityService.log_activity(
                    user_id=user.id,
                    activity_type='login',
                    request=request,
                    status='failed',
                    details={'error': 'Invalid password'}
                )
                return None, "Invalid username or password"
            
            if not user.is_active:
                ActivityService.log_activity(
                    user_id=user.id,
                    activity_type='login',
                    request=request,
                    status='failed',
                    details={'error': 'Account is deactivated'}
                )
                return None, "Account is deactivated"
            
            # Update last login timestamp
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            return user, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_user(user_id: int, update_data: Dict[str, Any]) -> Tuple[Optional[User], Optional[str]]:
        """Update user profile"""
        try:
            user = db.session.get(User, user_id)
            if not user:
                return None, "User not found"
            
            # Handle each field separately
            for field, value in update_data.items():
                if field == 'email' and value != user.email:
                    # Check if new email already exists
                    existing_email = User.query.filter_by(email=value).first()
                    if existing_email and existing_email.id != user_id:
                        return None, "Email already exists"
                    user.email = value
                elif field == 'first_name':
                    user.first_name = value
                elif field == 'last_name':
                    user.last_name = value
                elif field == 'password':
                    user.set_password(value)
                elif field == 'phone_number' and value != user.phone_number:
                    # Check if new phone number already exists
                    existing_phone = User.query.filter_by(phone_number=value).first()
                    if existing_phone and existing_phone.id != user_id:
                        return None, "Phone number already registered"
                    user.phone_number = value
            
            db.session.commit()
            return user, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_credits(user_id: int, amount: float, transaction_type: str, 
                      admin_id: int = None, reference_type: str = None, 
                      reference_id: str = None, notes: str = None) -> Tuple[Optional[User], Optional[str]]:
        """Update user's credit balance and record the transaction"""
        try:
            user = db.session.get(User, user_id)
            if not user:
                return None, "User not found"
            
            if transaction_type == 'subtract':
                amount = -abs(amount)
                if user.site_credits + amount < 0:
                    return None, "Insufficient credits"
            else:
                amount = abs(amount)
            
            transaction = CreditTransaction(
                user_id=user.id,
                amount=amount,
                transaction_type=transaction_type,
                balance_after=user.site_credits + amount,
                reference_type=reference_type,
                reference_id=reference_id,
                notes=notes,
                created_by_id=admin_id if admin_id else user_id
            )
            
            user.site_credits += amount
            
            db.session.add(transaction)
            db.session.commit()
            
            return user, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
        
    @staticmethod
    def get_all_users():
        """Get all users in the system"""
        try:
            return User.query.all()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Database error: {str(e)}")
        
    @staticmethod
    def update_user_status(user_id: int, admin_id: int, is_active: bool, reason: str):
        """Update user status and record the change"""
        try:
            user = db.session.get(User, user_id)
            if not user:
                return None, "User not found"
                
            admin = db.session.get(User, admin_id)
            if not admin or not admin.is_admin:
                return None, "Invalid admin user"
                
            if user.is_admin and not is_active:
                return None, "Cannot deactivate admin users"
                
            status_change = UserStatusChange(
                user_id=user.id,
                changed_by_id=admin_id,
                previous_status=user.is_active,
                new_status=is_active,
                reason=reason
            )
            
            user.is_active = is_active
            
            db.session.add(status_change)
            db.session.commit()
            
            return user, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
        
    @staticmethod
    def get_user_credit_transactions(user_id: int) -> Tuple[Optional[list], Optional[str]]:
        """Get credit transaction history for a user"""
        try:
            transactions = CreditTransaction.query\
                .filter_by(user_id=user_id)\
                .order_by(CreditTransaction.created_at.desc())\
                .all()
            return [t.to_dict() for t in transactions], None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def get_all_credit_transactions() -> Tuple[Optional[list], Optional[str]]:
        """Get all credit transactions (admin only)"""
        try:
            transactions = CreditTransaction.query\
                .order_by(CreditTransaction.created_at.desc())\
                .all()
            return [t.to_dict() for t in transactions], None
        except SQLAlchemyError as e:
            return None, str(e)

# Make sure UserService is available for import
__all__ = ['UserService']