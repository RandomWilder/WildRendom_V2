# src/prize_service/models/prize_instance.py

from enum import Enum
from datetime import datetime, timezone
from sqlalchemy.orm import validates, relationship
from src.shared import db

class InstanceStatus(str, Enum):
    AVAILABLE = 'available'
    DISCOVERED = 'discovered'
    CLAIMED = 'claimed'

class PrizeInstance(db.Model):
    """Model for prize instances in pools"""
    __tablename__ = 'prize_instances'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(100), unique=True, nullable=False)
    pool_id = db.Column(db.Integer, db.ForeignKey('prize_pools.id'), nullable=False)
    prize_id = db.Column(db.Integer, db.ForeignKey('prizes.id'), nullable=False)
    
    individual_odds = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=InstanceStatus.AVAILABLE.value)
    
    # Value fields we're missing
    retail_value = db.Column(db.Numeric(10, 2))
    cash_value = db.Column(db.Numeric(10, 2))
    credit_value = db.Column(db.Numeric(10, 2))
    
    claim_attempts = db.Column(db.Integer, default=0)
    max_claim_attempts = db.Column(db.Integer, default=3)
    claimed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    claimed_at = db.Column(db.DateTime)
    claim_deadline = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('status')
    def validate_status(self, key, status):
        """Validate status transitions"""
        if not hasattr(self, 'status'):
            self.status = InstanceStatus.AVAILABLE.value  # Set default
            return status

        valid_transitions = {
            InstanceStatus.AVAILABLE.value: [InstanceStatus.DISCOVERED.value],
            InstanceStatus.DISCOVERED.value: [InstanceStatus.CLAIMED.value, InstanceStatus.AVAILABLE.value],
            InstanceStatus.CLAIMED.value: []  # Terminal state
        }

        # Allow setting initial status
        if self.status is None:
            return status

        if status not in valid_transitions[self.status]:
            raise ValueError(f"Invalid status transition from {self.status} to {status}")

        return status

    def increment_claim_attempt(self):
        """Increment claim attempts and check limit"""
        self.claim_attempts += 1
        if self.claim_attempts >= self.max_claim_attempts:
            self.status = InstanceStatus.AVAILABLE.value
            return False
        return True

    def to_dict(self):
        """Convert instance to dictionary"""
        return {
            'instance_id': self.instance_id,
            'pool_id': self.pool_id,
            'prize_id': self.prize_id,
            'status': self.status,
            'individual_odds': self.individual_odds,
            'claim_attempts': self.claim_attempts,
            'claimed_by_id': self.claimed_by_id,
            'claimed_at': self.claimed_at.isoformat() if self.claimed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }