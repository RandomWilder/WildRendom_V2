# src/prize_service/models/prize.py

from enum import Enum
from datetime import datetime, timezone
from src.shared import db
from sqlalchemy.dialects.postgresql import JSON

class PrizeType(str, Enum):
    PHYSICAL = 'physical'
    DIGITAL = 'digital'
    CREDIT = 'credit'
    CUSTOM = 'custom'

class PrizeTier(str, Enum):
    PLATINUM = 'platinum'
    GOLD = 'gold'
    SILVER = 'silver'
    BRONZE = 'bronze'

class PrizeStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DEPLETED = 'depleted'
    DISCONTINUED = 'discontinued'

class Prize(db.Model):
    """Core prize definition model"""
    __tablename__ = 'prizes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Classification
    type = db.Column(db.String(20), nullable=False)
    custom_type = db.Column(db.String(50))
    tier = db.Column(db.String(20), nullable=False, default=PrizeTier.BRONZE.value)
    tier_priority = db.Column(db.Integer, default=0)
    
    # Values
    retail_value = db.Column(db.Numeric(10, 2), nullable=False)
    cash_value = db.Column(db.Numeric(10, 2), nullable=False)
    credit_value = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Inventory
    total_quantity = db.Column(db.Integer)
    available_quantity = db.Column(db.Integer)
    min_threshold = db.Column(db.Integer, default=0)
    
    # Tracking
    total_won = db.Column(db.Integer, default=0)
    total_claimed = db.Column(db.Integer, default=0)
    
    # Win Limits
    win_limit_per_user = db.Column(db.Integer, default=None)  # None means no limit
    win_limit_period_days = db.Column(db.Integer, default=None)  # None means lifetime
    
    # Status and Rules
    status = db.Column(db.String(20), nullable=False, default=PrizeStatus.ACTIVE.value)
    eligibility_rules = db.Column(JSON)  # Store complex eligibility rules as JSON
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.available_quantity is None and self.total_quantity:
            self.available_quantity = self.total_quantity

    def is_available(self) -> bool:
        """Check if prize is available for allocation"""
        return (
            self.status == PrizeStatus.ACTIVE.value
            and (self.available_quantity is None or self.available_quantity > 0)
        )

    def can_be_won_by_user(self, user_id: int) -> tuple[bool, str]:
        """Check if user is eligible to win this prize"""
        # TODO: Implement user win limit checks
        if not self.is_available():
            return False, "Prize is not available"
        return True, ""

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'custom_type': self.custom_type,
            'tier': self.tier,
            'tier_priority': self.tier_priority,
            'retail_value': float(self.retail_value),
            'cash_value': float(self.cash_value),
            'credit_value': float(self.credit_value),
            'total_quantity': self.total_quantity,
            'available_quantity': self.available_quantity,
            'min_threshold': self.min_threshold,
            'total_won': self.total_won,
            'total_claimed': self.total_claimed,
            'win_limit_per_user': self.win_limit_per_user,
            'win_limit_period_days': self.win_limit_period_days,
            'status': self.status,
            'eligibility_rules': self.eligibility_rules,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }