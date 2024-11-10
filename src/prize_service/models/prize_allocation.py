# src/prize_service/models/prize_allocation.py

from enum import Enum
from datetime import datetime, timezone, timedelta
from src.shared import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Index

class AllocationType(str, Enum):
    INSTANT_WIN = 'instant_win'
    RAFFLE_DRAW = 'draw_win'
    ADMIN_AWARD = 'admin_award'

class ClaimStatus(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    CLAIMED = 'claimed'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'

class PrizeAllocation(db.Model):
    """Enhanced prize allocation tracking"""
    __tablename__ = 'prize_allocations'
    __table_args__ = (
        Index('idx_allocation_reference', 'reference_type', 'reference_id'),
        Index('idx_allocation_user', 'winner_user_id', 'claim_status'),
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    prize_id = db.Column(db.Integer, db.ForeignKey('prizes.id'), nullable=False)
    pool_id = db.Column(db.Integer, db.ForeignKey('prize_pools.id'), nullable=False)
    
    # Allocation details
    allocation_type = db.Column(db.String(20), nullable=False)
    reference_type = db.Column(db.String(50), nullable=False)  # 'raffle', 'ticket'
    reference_id = db.Column(db.String(100), nullable=False)   # ID of raffle/ticket
    sequence_number = db.Column(db.Integer)  # For ordered draws
    
    # Winner tracking
    winner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    won_at = db.Column(db.DateTime)
    winning_odds = db.Column(db.Float)  # Actual odds at win time
    
    # Claim information
    claim_status = db.Column(db.String(20), default=ClaimStatus.PENDING.value)
    claim_deadline = db.Column(db.DateTime)
    claimed_at = db.Column(db.DateTime)
    claim_method = db.Column(db.String(20))  # Currently only 'credit'
    auto_claim_attempted = db.Column(db.Boolean, default=False)
    
    # Value tracking
    value_claimed = db.Column(db.Numeric(10, 2))
    original_value = db.Column(db.Numeric(10, 2))  # Value at time of win
    
    # Enhanced audit trail
    allocation_config = db.Column(JSON)  # Snapshot of configuration
    verification_code = db.Column(db.String(50))  # For claim verification
    claim_ip_address = db.Column(db.String(45))  # For security tracking
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'claim_status' not in kwargs:
            self.claim_status = ClaimStatus.PENDING.value
        if 'allocation_config' not in kwargs:
            self.allocation_config = {}

    def record_win(self, user_id: int, odds: float):
        """Record a prize win"""
        self.winner_user_id = user_id
        self.won_at = datetime.now(timezone.utc)
        self.winning_odds = odds
        
        # Set claim deadline based on prize configuration
        if self.prize:  # Assumes relationship with Prize model
            hours = self.prize.claim_deadline_hours or 24
            self.claim_deadline = self.won_at + timedelta(hours=hours)
            self.original_value = self.prize.credit_value  # Store original value

    def initiate_claim(self, claim_method: str = 'credit'):
        """Initiate prize claim process"""
        if self.claim_status != ClaimStatus.PENDING.value:
            raise ValueError(f"Cannot initiate claim in {self.claim_status} status")
            
        if datetime.now(timezone.utc) > self.claim_deadline:
            self.claim_status = ClaimStatus.EXPIRED.value
            raise ValueError("Claim deadline has passed")
            
        self.claim_method = claim_method
        self.claim_status = ClaimStatus.APPROVED.value

    def complete_claim(self, value_claimed: float, ip_address: str = None):
        """Complete a prize claim"""
        if self.claim_status != ClaimStatus.APPROVED.value:
            raise ValueError(f"Cannot complete claim in {self.claim_status} status")
            
        self.claim_status = ClaimStatus.CLAIMED.value
        self.claimed_at = datetime.now(timezone.utc)
        self.value_claimed = value_claimed
        self.claim_ip_address = ip_address

    def attempt_auto_claim(self) -> bool:
        """Attempt auto-claim for expiring prizes"""
        if self.auto_claim_attempted:
            return False
            
        if not self.prize.auto_claim_credit:
            return False
            
        time_remaining = self.claim_deadline - datetime.now(timezone.utc)
        if time_remaining.total_seconds() > 3600:  # More than 1 hour remaining
            return False
            
        try:
            self.initiate_claim('credit')
            self.complete_claim(self.original_value)
            self.auto_claim_attempted = True
            return True
        except:
            return False

    def to_dict(self):
        return {
            'id': self.id,
            'prize_id': self.prize_id,
            'pool_id': self.pool_id,
            'allocation_type': self.allocation_type,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'sequence_number': self.sequence_number,
            'winner_user_id': self.winner_user_id,
            'won_at': self.won_at.isoformat() if self.won_at else None,
            'winning_odds': self.winning_odds,
            'claim_status': self.claim_status,
            'claim_deadline': self.claim_deadline.isoformat() if self.claim_deadline else None,
            'claimed_at': self.claimed_at.isoformat() if self.claimed_at else None,
            'claim_method': self.claim_method,
            'value_claimed': float(self.value_claimed) if self.value_claimed else None,
            'original_value': float(self.original_value) if self.original_value else None,
            'verification_code': self.verification_code,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }