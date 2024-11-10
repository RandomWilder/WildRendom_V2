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
    INACTIVE = 'inactive'
    SOLD_OUT = 'sold_out'
    ENDED = 'ended'
    CANCELLED = 'cancelled'

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
    max_tickets_per_user = db.Column(db.Integer, nullable=False)
    
    # Prize pool integration
    prize_pool_id = db.Column(db.Integer, db.ForeignKey('prize_pools.id'), nullable=True)
    draw_count = db.Column(db.Integer, nullable=True)
    draw_distribution_type = db.Column(db.String(20), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    # Explicitly define the relationship with foreign_keys
    prize_pool = db.relationship(
        'PrizePool',
        foreign_keys=[prize_pool_id],
        backref=db.backref(
            'raffles',
            lazy=True,
            foreign_keys=[prize_pool_id]
        )
    )

    def __repr__(self):
        return f'<Raffle {self.title} ({self.status})>'
    
    def can_purchase_tickets(self) -> bool:
        """Check if tickets can be purchased"""
        current_time = datetime.now(timezone.utc)
        start_time = self.start_time if self.start_time.tzinfo else self.start_time.replace(tzinfo=timezone.utc)
        end_time = self.end_time if self.end_time.tzinfo else self.end_time.replace(tzinfo=timezone.utc)
        
        return (self.status == RaffleStatus.ACTIVE.value and
                current_time >= start_time and
                current_time < end_time)

    def validate_status_change(self, new_status: str) -> tuple[bool, str]:
        """Validate if a status change is allowed"""
        current_time = datetime.now(timezone.utc)
        start_time = self.start_time if self.start_time.tzinfo else self.start_time.replace(tzinfo=timezone.utc)
        end_time = self.end_time if self.end_time.tzinfo else self.end_time.replace(tzinfo=timezone.utc)

        if new_status == RaffleStatus.COMING_SOON.value and current_time >= start_time:
            return False, "Cannot set to Coming Soon after start time"
            
        if new_status == RaffleStatus.ACTIVE.value:
            if current_time < start_time:
                return False, "Cannot activate before start time"
            if current_time >= end_time:
                return False, "Cannot activate after end time"
            if not self.prize_pool_id:
                return False, "Cannot activate raffle without prize pool"

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
            'max_tickets_per_user': self.max_tickets_per_user,
            'prize_pool_id': self.prize_pool_id,
            'draw_configuration': {
                'number_of_draws': self.draw_count,
                'distribution_type': self.draw_distribution_type
            } if self.draw_count else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }