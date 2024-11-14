# src/raffle_service/models/ticket_reservation.py

from enum import Enum
from datetime import datetime, timezone
from src.shared import db

class ReservationStatus(str, Enum):
    PENDING = 'pending'
    ACTIVE = 'active'
    CONFIRMED = 'confirmed'
    COMPLETED = 'completed'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'

class TicketReservation(db.Model):
    """Model for temporary ticket reservations"""
    __tablename__ = 'ticket_reservations'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.String(50), primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)

    # Relationships with cascading deletes for proper cleanup
    raffle = db.relationship('Raffle', backref=db.backref('reservations', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('ticket_reservations', lazy='dynamic'))
    reserved_tickets = db.relationship(
        'ReservedTicket',
        backref='reservation',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.id:
            self.id = f"res_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{kwargs.get('user_id')}"

    def is_expired(self) -> bool:
        """Check if reservation has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def can_be_confirmed(self) -> bool:
        """Check if reservation can be confirmed"""
        return (
            self.status in [ReservationStatus.PENDING.value, ReservationStatus.ACTIVE.value] and
            not self.is_expired()
        )

class ReservedTicket(db.Model):
    """Model for individual tickets in a reservation"""
    __tablename__ = 'reserved_tickets'
    __table_args__ = {'extend_existing': True}

    reservation_id = db.Column(db.String(50), 
                             db.ForeignKey('ticket_reservations.id', ondelete='CASCADE'),
                             primary_key=True)
    ticket_id = db.Column(db.Integer, 
                         db.ForeignKey('tickets.id'),
                         primary_key=True)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to ticket with cascade for proper cleanup
    ticket = db.relationship(
        'Ticket',
        backref=db.backref('reservation', uselist=False)
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not kwargs.get('status'):
            self.status = ReservationStatus.PENDING.value