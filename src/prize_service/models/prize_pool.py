# src/prize_service/models/prize_pool.py

from enum import Enum
from datetime import datetime, timezone
from src.shared import db
from sqlalchemy.dialects.postgresql import JSON

class PoolStatus(str, Enum):
    DRAFT = 'draft'
    ACTIVE = 'active'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class AllocationStrategy(str, Enum):
    DYNAMIC = 'dynamic'
    PRE_ALLOCATED = 'pre_allocated'
    ADMIN_ASSIGNED = 'admin_assigned'

class PrizePool(db.Model):
    """Prize pool for managing collections of prizes"""
    __tablename__ = 'prize_pools'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Pool configuration
    status = db.Column(db.String(20), nullable=False, default=PoolStatus.DRAFT.value)
    allocation_strategy = db.Column(db.String(20), nullable=False, default=AllocationStrategy.DYNAMIC.value)
    
    # Time constraints
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    
    # Budget tracking
    budget_limit = db.Column(db.Numeric(10, 2))
    current_allocation = db.Column(db.Numeric(10, 2), default=0)
    
    # Configuration
    allocation_rules = db.Column(JSON)
    win_limits = db.Column(JSON)
    eligibility_rules = db.Column(JSON)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def is_active(self) -> bool:
        """Check if pool is currently active"""
        now = datetime.now(timezone.utc)
        return (
            self.status == PoolStatus.ACTIVE.value
            and self.start_date <= now <= self.end_date
        )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'allocation_strategy': self.allocation_strategy,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'budget_limit': float(self.budget_limit) if self.budget_limit else None,
            'current_allocation': float(self.current_allocation),
            'allocation_rules': self.allocation_rules,
            'win_limits': self.win_limits,
            'eligibility_rules': self.eligibility_rules,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }