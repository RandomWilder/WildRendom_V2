# src/raffle_service/models/raffle.py
from datetime import datetime, timezone
from src.shared import db
from enum import Enum
from typing import Optional
import logging

class RaffleStatus(str, Enum):
    DRAFT = 'draft'
    COMING_SOON = 'coming_soon'
    ACTIVE = 'active'
    INACTIVE = 'inactive'  # Replaces PAUSED
    SOLD_OUT = 'sold_out'
    ENDED = 'ended'
    CANCELLED = 'cancelled'

    @classmethod
    def get_display_statuses(cls) -> list[str]:
        """Get statuses that are visible to public"""
        return [
            cls.COMING_SOON.value,
            cls.ACTIVE.value,
            cls.SOLD_OUT.value,
            cls.ENDED.value
        ]

    @classmethod
    def get_purchasable_statuses(cls) -> list[str]:
        """Get statuses where ticket purchase is allowed"""
        return [cls.ACTIVE.value]

class Raffle(db.Model):
    """Core raffle model with enhanced lifecycle management"""
    __tablename__ = 'raffles'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    total_tickets = db.Column(db.Integer, nullable=False)
    ticket_price = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=RaffleStatus.DRAFT.value)
    max_tickets_per_user = db.Column(db.Integer, nullable=False, default=10)
    
    # Prize configuration
    total_prize_count = db.Column(db.Integer, nullable=False)
    instant_win_count = db.Column(db.Integer, default=0)
    prize_structure = db.Column(db.JSON, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    # Prize placeholders and instant win configuration
    total_prize_count = db.Column(db.Integer, nullable=False)
    instant_win_count = db.Column(db.Integer, default=0)
    prize_structure = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f'<Raffle {self.title} ({self.status})>'

    def is_visible_to_public(self) -> bool:
        """Check if raffle is visible to public"""
        return self.status in RaffleStatus.get_display_statuses()

    def can_purchase_tickets(self) -> bool:
        """Check if tickets can be purchased"""
        return self.status in RaffleStatus.get_purchasable_statuses()

    def compute_current_status(self) -> Optional[str]:
        """Compute what the status should be based on current conditions"""
        current_time = datetime.now(timezone.utc)
        end_time = self.end_time if self.end_time.tzinfo else self.end_time.replace(tzinfo=timezone.utc)
        
        # Terminal states
        if self.status in [RaffleStatus.CANCELLED.value, RaffleStatus.ENDED.value]:
            return self.status

        # Time-based transitions
        if current_time >= end_time:
            return RaffleStatus.ENDED.value
            
        # Check for sold out condition
        if hasattr(self, 'tickets'):
            available_tickets = sum(1 for t in self.tickets if t.status == 'available')
            if available_tickets == 0 and self.status != RaffleStatus.DRAFT.value:
                return RaffleStatus.SOLD_OUT.value

        return None  # No automatic status change needed

    def validate_status_change(self, new_status: str) -> tuple[bool, str]:
        """Validate if a status change is allowed"""
        # Ensure all times are timezone aware
        current_time = datetime.now(timezone.utc)
        start_time = self.start_time if self.start_time.tzinfo else self.start_time.replace(tzinfo=timezone.utc)
        end_time = self.end_time if self.end_time.tzinfo else self.end_time.replace(tzinfo=timezone.utc)

        # Time validations
        if new_status == RaffleStatus.COMING_SOON.value:
            if current_time >= start_time:
                return False, "Cannot set to Coming Soon after start time"
                
        elif new_status == RaffleStatus.ACTIVE.value:
            if current_time < start_time:
                return False, "Cannot activate before start time"
            if current_time >= end_time:
                return False, "Cannot activate after end time"

        return True, ""

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'total_tickets': self.total_tickets,
            'ticket_price': self.ticket_price,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'total_prize_count': self.total_prize_count,
            'instant_win_count': self.instant_win_count,
            'prize_structure': self.prize_structure,
            'max_tickets_per_user': self.max_tickets_per_user,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by_id': self.created_by_id,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_visible': self.is_visible_to_public(),
            'can_purchase': self.can_purchase_tickets()
        }
    
    def __init__(self, **kwargs):
        # Ensure timezone awareness for datetime fields
        if 'start_time' in kwargs and kwargs['start_time'].tzinfo is None:
            kwargs['start_time'] = kwargs['start_time'].replace(tzinfo=timezone.utc)
        if 'end_time' in kwargs and kwargs['end_time'].tzinfo is None:
            kwargs['end_time'] = kwargs['end_time'].replace(tzinfo=timezone.utc)
        super().__init__(**kwargs)