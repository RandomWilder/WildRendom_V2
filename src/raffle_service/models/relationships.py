# src/raffle_service/models/relationships.py

from src.shared import db
from .raffle import Raffle
from .ticket import Ticket
from .instant_win import InstantWin
from .user_raffle_stats import UserRaffleStats

# Raffle relationships
Raffle.tickets = db.relationship('Ticket',
                               backref=db.backref('raffle', lazy=True),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

Raffle.created_by = db.relationship('User',
                                  foreign_keys=[Raffle.created_by_id],
                                  backref=db.backref('raffles_created', lazy=True))

# Instant win relationships
Raffle.instant_wins = db.relationship('InstantWin',
                                   backref=db.backref('raffle', lazy=True),
                                   lazy='dynamic',
                                   cascade='save-update')  # Preserve records for audit

# Ticket relationships
Ticket.instant_win_entry = db.relationship('InstantWin',
                                        backref=db.backref('ticket', lazy=True),
                                        uselist=False,  # One-to-one relationship
                                        cascade='save-update')  # Preserve records for audit