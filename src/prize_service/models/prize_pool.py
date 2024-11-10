# src/prize_service/models/prize_pool.py

from enum import Enum
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import validates, relationship
from src.shared import db
import logging

logger = logging.getLogger(__name__)

class PoolStatus(str, Enum):
    UNLOCKED = 'unlocked'
    LOCKED = 'locked'
    USED = 'used'

class PrizePool(db.Model):
    """Prize Pool model with enhanced instance tracking"""
    __tablename__ = 'prize_pools'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default=PoolStatus.UNLOCKED.value)
    
    # Instance tracking
    total_instances = db.Column(db.Integer, default=0)
    available_instances = db.Column(db.Integer, default=0)
    instant_win_count = db.Column(db.Integer, default=0)
    draw_win_count = db.Column(db.Integer, default=0)
    
    # Value tracking
    total_value = db.Column(db.Numeric(10, 2), default=0)
    retail_total = db.Column(db.Numeric(10, 2), default=0)
    cash_total = db.Column(db.Numeric(10, 2), default=0)
    credit_total = db.Column(db.Numeric(10, 2), default=0)
    
    # Relationships
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffles.id'), unique=True)
    instances = relationship('PrizeInstance', backref='pool', lazy='dynamic')
    
    # Timestamps and audit
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('status')
    def validate_status(self, key, status):
        """Validate status transitions"""
        if not hasattr(self, 'status'):
            return status
            
        old_status = self.status
        
        # Validation rules
        if old_status == PoolStatus.USED.value:
            raise ValueError("Cannot change status of USED pool")
            
        if status == PoolStatus.USED.value and old_status != PoolStatus.LOCKED.value:
            raise ValueError("Pool must be LOCKED before being USED")
            
        return status

    def check_can_unlock(self):
        """Check if pool can be unlocked"""
        if self.raffle_id:
            from src.raffle_service.models import Raffle
            raffle = Raffle.query.get(self.raffle_id)
            if raffle and raffle.status != 'draft':
                return False
        return True

    def calculate_odds_total(self):
        """Calculate total odds across all instances"""
        return sum(instance.individual_odds for instance in self.instances)

    def validate_for_lock(self):
        """Validate pool can be locked"""
        # Check has instances
        if self.total_instances == 0:
            return False, "No prize instances allocated"
            
        # Check has draw win
        if self.draw_win_count == 0:
            return False, "Must have at least one Draw Win prize"
            
        # Validate odds total
        odds_total = self.calculate_odds_total()
        if abs(odds_total - 100.0) > 0.0001:
            return False, f"Total odds must be 100% (current: {odds_total}%)"
            
        return True, None

    def to_dict(self):
        """Convert pool to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'total_instances': self.total_instances,
            'instant_win_instances': self.instant_win_count,
            'draw_win_instances': self.draw_win_count,
            'values': {
                'retail_total': float(self.retail_total),
                'cash_total': float(self.cash_total),
                'credit_total': float(self.credit_total)
            },
            'total_odds': self.calculate_odds_total(),
            'assigned_to_raffle_id': self.raffle_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
