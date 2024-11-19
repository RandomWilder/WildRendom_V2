# src/user_service/models/__init__.py

from .user import User
from .user_status import UserStatusChange
from .credit_transaction import CreditTransaction
from .user_activity import UserActivity
from .user_tier import UserTier, UserTierHistory, TierLevel  # Add new models

__all__ = [
    'User', 
    'UserStatusChange', 
    'CreditTransaction', 
    'UserActivity',
    'UserTier',
    'UserTierHistory',
    'TierLevel'
]