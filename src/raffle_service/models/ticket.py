# src/raffle_service/models/ticket.py
from datetime import datetime, timezone
from src.shared import db
from enum import Enum
from sqlalchemy import Index

class TicketStatus(str, Enum):
    AVAILABLE = 'available'
    SOLD = 'sold'
    CANCELLED = 'cancelled'
    VOID = 'void'

class Ticket(db.Model):
    """Ticket model for raffles"""
    __tablename__ = 'tickets'
    __table_args__ = (
        Index('idx_ticket_id', 'ticket_id', unique=True),
        Index('idx_ticket_raffle_number', 'raffle_id', 'ticket_number', unique=True),
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffles.id'), nullable=False)
    ticket_id = db.Column(db.String(20), nullable=False, unique=True)
    ticket_number = db.Column(db.String(3), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    purchase_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=TicketStatus.AVAILABLE.value)
    instant_win = db.Column(db.Boolean, default=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('credit_transactions.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def formatted_ticket_id(self) -> str:
        """Generate the formatted ticket ID"""
        return f"{self.raffle_id}-{self.ticket_number}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ticket_id and self.raffle_id and self.ticket_number:
            self.ticket_id = self.formatted_ticket_id

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'ticket_number': self.ticket_number,
            'raffle_id': self.raffle_id,
            'user_id': self.user_id,
            'purchase_time': self.purchase_time.isoformat() if self.purchase_time else None,
            'status': self.status,
            'instant_win': self.instant_win,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }