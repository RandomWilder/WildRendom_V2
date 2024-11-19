from datetime import datetime, timezone, timedelta
from src.shared import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Dict

class User(db.Model):
    """User model for storing user related details"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    site_credits = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    auth_provider = db.Column(db.String(20), default='local')
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # New tier-related properties
    _tier_benefits_cache = None
    _tier_benefits_timestamp = None
    TIER_CACHE_DURATION = timedelta(minutes=5)  # Cache tier benefits for 5 minutes
    
    @hybrid_property
    def requires_password(self):
        """Check if user requires password based on auth provider"""
        return self.auth_provider == 'local'
    
    def set_password(self, password):
        """Set password hash - only for local auth"""
        if self.requires_password and password:
            self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password - only for local auth"""
        if not self.requires_password:
            return False
        return self.password_hash and check_password_hash(self.password_hash, password)

    @property
    def tier_benefits(self) -> Dict:
        """Get user's current tier benefits with caching"""
        current_time = datetime.now(timezone.utc)
        
        # Return cached benefits if still valid
        if (self._tier_benefits_cache is not None and 
            self._tier_benefits_timestamp is not None and
            current_time - self._tier_benefits_timestamp < self.TIER_CACHE_DURATION):
            return self._tier_benefits_cache

        # Get fresh benefits
        from src.user_service.services.tier_service import TierService
        tier_info, _ = TierService.get_user_tier(self.id)
        
        # Set default benefits if no tier info found
        if not tier_info:
            self._tier_benefits_cache = {
                'purchase_limit_multiplier': 1.0,
                'early_access_hours': 0,
                'has_exclusive_access': False,
                'current_tier': 'bronze'
            }
        else:
            self._tier_benefits_cache = {
                'purchase_limit_multiplier': tier_info.get('purchase_limit_multiplier', 1.0),
                'early_access_hours': tier_info.get('early_access_hours', 0),
                'has_exclusive_access': tier_info.get('has_exclusive_access', False),
                'current_tier': tier_info.get('current_tier', 'bronze')
            }

        self._tier_benefits_timestamp = current_time
        return self._tier_benefits_cache

    def get_adjusted_purchase_limit(self, base_limit: int) -> int:
        """Get purchase limit adjusted by tier multiplier"""
        multiplier = self.tier_benefits.get('purchase_limit_multiplier', 1.0)
        return int(base_limit * multiplier)

    def can_access_early(self, raffle_start: datetime) -> bool:
        """Check if user has early access to raffle"""
        early_hours = self.tier_benefits.get('early_access_hours', 0)
        if early_hours <= 0:
            return False
        
        current_time = datetime.now(timezone.utc)
        early_access_time = raffle_start - timedelta(hours=early_hours)
        return current_time >= early_access_time

    def to_dict(self):
        """Convert user to dictionary with tier information"""
        base_dict = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'auth_provider': self.auth_provider,
            'verification_status': {
                'is_verified': self.is_verified,
                'email_verified': self.is_verified,
                'phone_verified': False,
            },
            'site_credits': self.site_credits,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

        # Add tier information
        base_dict['tier'] = {
            'current_tier': self.tier_benefits.get('current_tier', 'bronze'),
            'benefits': {
                'purchase_limit_multiplier': self.tier_benefits.get('purchase_limit_multiplier', 1.0),
                'early_access_hours': self.tier_benefits.get('early_access_hours', 0),
                'has_exclusive_access': self.tier_benefits.get('has_exclusive_access', False)
            }
        }

        return base_dict