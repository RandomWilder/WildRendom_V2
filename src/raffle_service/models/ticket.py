# src/raffle_service/models/ticket.py
from datetime import datetime, timezone
from src.shared import db
from enum import Enum
from sqlalchemy import Index, event

class TicketStatus(str, Enum):
    AVAILABLE = 'available'
    SOLD = 'sold'
    REVEALED = 'revealed'    # New status for revealed tickets
    CANCELLED = 'cancelled'
    VOID = 'void'

class Ticket(db.Model):
    """Ticket model for raffles with enhanced reveal mechanism"""
    __tablename__ = 'tickets'
    __table_args__ = (
        Index('idx_ticket_id', 'ticket_id', unique=True),
        Index('idx_ticket_raffle_number', 'raffle_id', 'ticket_number', unique=True),
        Index('idx_ticket_reveal', 'raffle_id', 'user_id', 'reveal_time'),  # New index for reveal queries
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffles.id'), nullable=False)
    ticket_id = db.Column(db.String(20), nullable=False, unique=True)
    ticket_number = db.Column(db.String(3), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    purchase_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=TicketStatus.AVAILABLE.value)
    
    # Enhanced reveal mechanism
    is_revealed = db.Column(db.Boolean, default=False)
    reveal_time = db.Column(db.DateTime, nullable=True)
    reveal_sequence = db.Column(db.Integer, nullable=True)  # For ordered reveals
    
    # Instant win configuration
    instant_win = db.Column(db.Boolean, default=False)
    instant_win_eligible = db.Column(db.Boolean, default=False)  # New field
    transaction_id = db.Column(db.Integer, db.ForeignKey('credit_transactions.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ticket_id and self.raffle_id and self.ticket_number:
            self.ticket_id = self.formatted_ticket_id

    @property
    def formatted_ticket_id(self) -> str:
        """Generate the formatted ticket ID"""
        return f"{self.raffle_id}-{self.ticket_number}"

    def reveal(self) -> bool:
        """
        Reveal the ticket
        Returns: True if successful, False if already revealed
        """
        if self.is_revealed:
            return False
            
        if self.status != TicketStatus.SOLD.value:
            raise ValueError("Only sold tickets can be revealed")

        self.is_revealed = True
        self.reveal_time = datetime.now(timezone.utc)
        self.status = TicketStatus.REVEALED.value
        
        return True

    def mark_instant_win_eligible(self):
        """Mark ticket as eligible for instant win"""
        if self.status != TicketStatus.AVAILABLE.value:
            raise ValueError("Only available tickets can be marked as instant win eligible")
            
        self.instant_win_eligible = True

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'ticket_number': self.ticket_number,
            'raffle_id': self.raffle_id,
            'user_id': self.user_id,
            'purchase_time': self.purchase_time.isoformat() if self.purchase_time else None,
            'status': self.status,
            'is_revealed': self.is_revealed,
            'reveal_time': self.reveal_time.isoformat() if self.reveal_time else None,
            'reveal_sequence': self.reveal_sequence,
            'instant_win': self.instant_win,
            'instant_win_eligible': self.instant_win_eligible,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# SQLAlchemy event listeners for ticket status changes
@event.listens_for(Ticket.status, 'set')
def ticket_status_change(target, value, oldvalue, initiator):
    """Handle ticket status changes"""
    if oldvalue == value:
        return
        
    if value == TicketStatus.REVEALED.value:
        target.reveal_time = datetime.now(timezone.utc)