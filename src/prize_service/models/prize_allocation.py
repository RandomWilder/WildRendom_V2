# src/prize_service/models/prize_allocation.py

from enum import Enum
from datetime import datetime, timezone
from src.shared import db
from sqlalchemy.dialects.postgresql import JSON

class AllocationType(str, Enum):
    RAFFLE = 'raffle'
    INSTANT_WIN = 'instant_win'
    ADMIN = 'admin'

class ClaimStatus(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    CLAIMED = 'claimed'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'

class PrizeAllocation(db.Model):
    """Tracks prize allocations to raffles/tickets"""
    __tablename__ = 'prize_allocations'

    id = db.Column(db.Integer, primary_key=True)
    prize_id = db.Column(db.Integer, db.ForeignKey('prizes.id'), nullable=False)
    pool_id = db.Column(db.Integer, db.ForeignKey('prize_pools.id'), nullable=False)
    
    # Allocation details
    allocation_type = db.Column(db.String(20), nullable=False)
    reference_type = db.Column(db.String(50))  # 'raffle', 'ticket', etc.
    reference_id = db.Column(db.String(100))   # Actual ID of raffle/ticket
    
    # Winner tracking
    winner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    won_at = db.Column(db.DateTime)
    
    # Claim information
    claim_status = db.Column(db.String(20))
    claim_deadline = db.Column(db.DateTime)
    claimed_at = db.Column(db.DateTime)
    claim_method = db.Column(db.String(20))  # 'cash', 'prize', 'credit'
    
    # Value tracking
    value_claimed = db.Column(db.Numeric(10, 2))
    
    # Configuration and metadata
    allocation_config = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'prize_id': self.prize_id,
            'pool_id': self.pool_id,
            'allocation_type': self.allocation_type,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'winner_user_id': self.winner_user_id,
            'won_at': self.won_at.isoformat() if self.won_at else None,
            'claim_status': self.claim_status,
            'claim_deadline': self.claim_deadline.isoformat() if self.claim_deadline else None,
            'claimed_at': self.claimed_at.isoformat() if self.claimed_at else None,
            'claim_method': self.claim_method,
            'value_claimed': float(self.value_claimed) if self.value_claimed else None,
            'allocation_config': self.allocation_config,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PrizePoolAllocation(db.Model):
    """Maps prizes to pools with allocation rules"""
    __tablename__ = 'prize_pool_allocations'

    id = db.Column(db.Integer, primary_key=True)
    pool_id = db.Column(db.Integer, db.ForeignKey('prize_pools.id'), nullable=False)
    prize_id = db.Column(db.Integer, db.ForeignKey('prizes.id'), nullable=False)
    
    quantity_allocated = db.Column(db.Integer, nullable=False)
    quantity_remaining = db.Column(db.Integer, nullable=False)
    allocation_rules = db.Column(JSON)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.quantity_remaining is None:
            self.quantity_remaining = self.quantity_allocated

    def to_dict(self):
        return {
            'id': self.id,
            'pool_id': self.pool_id,
            'prize_id': self.prize_id,
            'quantity_allocated': self.quantity_allocated,
            'quantity_remaining': self.quantity_remaining,
            'allocation_rules': self.allocation_rules,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }