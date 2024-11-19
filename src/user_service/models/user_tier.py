# src/user_service/models/user_tier.py

from enum import Enum
from datetime import datetime, timezone
from src.shared import db
from sqlalchemy.orm import relationship
from sqlalchemy import event

class TierLevel(str, Enum):
    BRONZE = 'bronze'
    SILVER = 'silver'
    GOLD = 'gold'
    PLATINUM = 'platinum'

class UserTier(db.Model):
    """User tier tracking and management"""
    __tablename__ = 'user_tiers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    current_tier = db.Column(db.String(20), nullable=False, default=TierLevel.BRONZE.value)
    
    # Qualification metrics
    total_spent = db.Column(db.Float, default=0.0)
    total_participations = db.Column(db.Integer, default=0)
    total_wins = db.Column(db.Integer, default=0)
    
    # Rolling period metrics (last 90 days)
    spend_90d = db.Column(db.Float, default=0.0)
    participations_90d = db.Column(db.Integer, default=0)
    wins_90d = db.Column(db.Integer, default=0)
    
    # Tier status
    tier_updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_activity_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Benefits tracking
    purchase_limit_multiplier = db.Column(db.Float, default=1.0)
    early_access_hours = db.Column(db.Integer, default=0)
    has_exclusive_access = db.Column(db.Boolean, default=False)
    
    # Tier history for auditing
    tier_history = relationship("UserTierHistory", backref="user_tier", lazy='dynamic')

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.update_benefits()

    def update_benefits(self):
        """Update user benefits based on current tier"""
        benefits = {
            TierLevel.BRONZE.value: {
                'multiplier': 1.0,
                'early_access': 0,
                'exclusive': False
            },
            TierLevel.SILVER.value: {
                'multiplier': 1.1,
                'early_access': 0,
                'exclusive': False
            },
            TierLevel.GOLD.value: {
                'multiplier': 1.25,
                'early_access': 12,
                'exclusive': True
            },
            TierLevel.PLATINUM.value: {
                'multiplier': 1.5,
                'early_access': 24,
                'exclusive': True
            }
        }
        
        tier_benefit = benefits[self.current_tier]
        self.purchase_limit_multiplier = tier_benefit['multiplier']
        self.early_access_hours = tier_benefit['early_access']
        self.has_exclusive_access = tier_benefit['exclusive']

    def evaluate_tier(self) -> bool:
        """
        Evaluate and update user's tier based on activity
        Returns: True if tier changed
        """
        old_tier = self.current_tier
        
        # Determine new tier based on criteria
        if self.qualify_for_platinum():
            new_tier = TierLevel.PLATINUM.value
        elif self.qualify_for_gold():
            new_tier = TierLevel.GOLD.value
        elif self.qualify_for_silver():
            new_tier = TierLevel.SILVER.value
        else:
            new_tier = TierLevel.BRONZE.value
            
        # Update if changed
        if new_tier != old_tier:
            self.current_tier = new_tier
            self.tier_updated_at = datetime.now(timezone.utc)
            self.update_benefits()
            
            # Record history
            history = UserTierHistory(
                user_tier_id=self.id,
                previous_tier=old_tier,
                new_tier=new_tier
            )
            db.session.add(history)
            return True
            
        return False

    def qualify_for_platinum(self) -> bool:
        return (
            self.spend_90d >= 2000 or
            (self.participations_90d >= 30 and self.wins_90d >= 2)
        )

    def qualify_for_gold(self) -> bool:
        return (
            self.spend_90d >= 500 or
            (self.participations_90d >= 15 and self.wins_90d >= 1)
        )

    def qualify_for_silver(self) -> bool:
        return (
            self.spend_90d >= 100 or
            self.participations_90d >= 5
        )

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'current_tier': self.current_tier,
            'stats': {
                'total_spent': self.total_spent,
                'total_participations': self.total_participations,
                'total_wins': self.total_wins,
                'recent_spend': self.spend_90d,
                'recent_participations': self.participations_90d,
                'recent_wins': self.wins_90d
            },
            'benefits': {
                'purchase_limit_multiplier': self.purchase_limit_multiplier,
                'early_access_hours': self.early_access_hours,
                'has_exclusive_access': self.has_exclusive_access
            },
            'tier_updated_at': self.tier_updated_at.isoformat(),
            'last_activity_date': self.last_activity_date.isoformat()
        }

class UserTierHistory(db.Model):
    """Track tier change history"""
    __tablename__ = 'user_tier_history'

    id = db.Column(db.Integer, primary_key=True)
    user_tier_id = db.Column(db.Integer, db.ForeignKey('user_tiers.id'), nullable=False)
    previous_tier = db.Column(db.String(20), nullable=False)
    new_tier = db.Column(db.String(20), nullable=False)
    changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'user_tier_id': self.user_tier_id,
            'previous_tier': self.previous_tier,
            'new_tier': self.new_tier,
            'changed_at': self.changed_at.isoformat()
        }

# Add relationship to User model
from src.user_service.models.user import User
User.tier = relationship("UserTier", uselist=False, backref="user")