# src/raffle_service/models/instant_win.py

from datetime import datetime, timezone, timedelta
from enum import Enum
from src.shared import db
from sqlalchemy.orm import validates
from sqlalchemy import Index, UniqueConstraint

class InstantWinStatus(str, Enum):
    ALLOCATED = 'allocated'      # Assigned to ticket, not yet discovered
    DISCOVERED = 'discovered'    # User bought winning ticket
    PENDING_CLAIM = 'pending'    # User notified, hasn't claimed
    CLAIMED = 'claimed'         # User has claimed prize
    EXPIRED = 'expired'         # Claim window expired

class InstantWin(db.Model):
    """Tracks instant win prizes and their status"""
    __tablename__ = 'instant_wins'
    
    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffles.id', ondelete='RESTRICT'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id', ondelete='RESTRICT'), nullable=False)
    
    # Add the relationship (though it will be managed by the backref from Ticket)
    ticket = db.relationship('Ticket', backref=db.backref('instant_win_entry', lazy=True, uselist=False))
    
    # Prize placeholder (for Prize Service integration)
    prize_reference = db.Column(db.String(100), nullable=False)
    
    # Status tracking
    status = db.Column(db.String(20), nullable=False, default=InstantWinStatus.ALLOCATED.value)
    discovered_at = db.Column(db.DateTime, nullable=True)
    claim_deadline = db.Column(db.DateTime, nullable=True)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('ticket_id', name='uq_one_win_per_ticket'),
        Index('ix_instant_wins_raffle_id_status', 'raffle_id', 'status'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'status' not in kwargs:
            self.status = InstantWinStatus.ALLOCATED.value
    
    @validates('status')
    def validate_status_change(self, key, value):
        """Prevent invalid status transitions"""
        valid_transitions = {
            InstantWinStatus.ALLOCATED.value: [InstantWinStatus.DISCOVERED.value],
            InstantWinStatus.DISCOVERED.value: [InstantWinStatus.PENDING_CLAIM.value, InstantWinStatus.EXPIRED.value],
            InstantWinStatus.PENDING_CLAIM.value: [InstantWinStatus.CLAIMED.value, InstantWinStatus.EXPIRED.value],
            InstantWinStatus.CLAIMED.value: [],  # Terminal state
            InstantWinStatus.EXPIRED.value: []   # Terminal state
        }
        
        if hasattr(self, 'status') and self.status:
            if value not in valid_transitions.get(self.status, []):
                raise ValueError(f"Invalid status transition from {self.status} to {value}")
        
        return value
    
    def discover(self):
        """Mark instant win as discovered when ticket is purchased"""
        self.status = InstantWinStatus.DISCOVERED.value
        self.discovered_at = datetime.now(timezone.utc)
        # Set claim deadline (e.g., 24 hours from discovery)
        self.claim_deadline = self.discovered_at + timedelta(hours=24)
    
    def mark_pending_claim(self):
        """Mark instant win as pending claim (waiting for Prize Service)"""
        self.status = InstantWinStatus.PENDING_CLAIM.value
    
    def mark_claimed(self):
        """Mark instant win as claimed (Prize Service confirmed)"""
        self.status = InstantWinStatus.CLAIMED.value
    
    def mark_expired(self):
        """Mark instant win as expired (claim window passed)"""
        self.status = InstantWinStatus.EXPIRED.value
    
    def to_dict(self):
        return {
            'id': self.id,
            'raffle_id': self.raffle_id,
            'ticket_id': self.ticket_id,
            'prize_reference': self.prize_reference,
            'status': self.status,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'claim_deadline': self.claim_deadline.isoformat() if self.claim_deadline else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }