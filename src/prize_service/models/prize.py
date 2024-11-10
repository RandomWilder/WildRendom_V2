# src/prize_service/models/prize.py

from datetime import datetime, timezone
from src.shared import db
from enum import Enum

class PrizeType(str, Enum):
    INSTANT_WIN = 'Instant_Win'
    DRAW_WIN = 'Draw_Win'
    PROMOTIONAL = 'Promotional'
    CUSTOM = 'Custom'

class PrizeStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DEPLETED = 'depleted'
    EXPIRED = 'expired'

class PrizeTier(str, Enum):
    PLATINUM = 'platinum'
    GOLD = 'gold'
    SILVER = 'silver'
    BRONZE = 'bronze'

class Prize(db.Model):
    """Prize model - defines what a prize IS"""
    __tablename__ = 'prizes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(20), nullable=False)
    tier = db.Column(db.String(20), nullable=False)
    tier_priority = db.Column(db.Integer, default=0)
    retail_value = db.Column(db.Numeric(10, 2), nullable=False)
    cash_value = db.Column(db.Numeric(10, 2), nullable=False)
    credit_value = db.Column(db.Numeric(10, 2), nullable=False)
    expiry_days = db.Column(db.Integer, nullable=False, default=7)
    claim_processor_type = db.Column(db.String(20), nullable=False, default='credit')
    claim_deadline_hours = db.Column(db.Integer, nullable=True)
    auto_claim_credit = db.Column(db.Boolean, default=False)
    total_quantity = db.Column(db.Integer, nullable=True)
    available_quantity = db.Column(db.Integer, nullable=True)
    total_allocated = db.Column(db.Integer, default=0)
    total_claimed = db.Column(db.Integer, default=0)
    win_limit_per_user = db.Column(db.Integer, nullable=True)
    win_limit_period_days = db.Column(db.Integer, nullable=True)
    win_odds = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), nullable=False, default=PrizeStatus.ACTIVE.value)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.status:
            self.status = PrizeStatus.ACTIVE.value

    def to_dict(self):
        """Convert prize to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'tier': self.tier,
            'tier_priority': self.tier_priority,
            'retail_value': float(self.retail_value),
            'cash_value': float(self.cash_value),
            'credit_value': float(self.credit_value),
            'expiry_days': self.expiry_days,
            'claim_processor_type': self.claim_processor_type,
            'auto_claim_credit': self.auto_claim_credit,
            'total_quantity': self.total_quantity,
            'available_quantity': self.available_quantity,
            'total_claimed': self.total_claimed,
            'total_allocated': self.total_allocated,
            'claim_deadline_hours': self.claim_deadline_hours,
            'win_limit_per_user': self.win_limit_per_user,
            'win_limit_period_days': self.win_limit_period_days,
            'win_odds': self.win_odds,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }