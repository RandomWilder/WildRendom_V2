# src/prize_service/models/prize_pool.py

from enum import Enum
from datetime import datetime, timezone
from src.shared import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import validates
import json

class PoolStatus(str, Enum):
    DRAFT = 'draft'
    ACTIVE = 'active'
    LOCKED = 'locked'      # New status for locked pools
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class AllocationStrategy(str, Enum):
    DYNAMIC = 'dynamic'
    PRE_ALLOCATED = 'pre_allocated'
    ODDS_BASED = 'odds_based'    # New strategy for odds-based allocation
    ADMIN_ASSIGNED = 'admin_assigned'

class PrizePool(db.Model):
    """Prize pool for managing collections of prizes"""
    __tablename__ = 'prize_pools'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Pool configuration
    status = db.Column(db.String(20), nullable=False, default=PoolStatus.DRAFT.value)
    allocation_strategy = db.Column(db.String(20), nullable=False, default=AllocationStrategy.ODDS_BASED.value)
    is_locked = db.Column(db.Boolean, default=False)  # New field for pool locking
    
    # Time constraints
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    
    # Enhanced prize configuration
    odds_configuration = db.Column(JSON)  # Store prize odds and quantities
    total_prizes = db.Column(db.Integer, default=0)
    available_prizes = db.Column(db.Integer, default=0)
    
    # Budget tracking
    budget_limit = db.Column(db.Numeric(10, 2))
    current_allocation = db.Column(db.Numeric(10, 2), default=0)
    total_value = db.Column(db.Numeric(10, 2), default=0)
    
    # Configuration
    allocation_rules = db.Column(JSON)
    win_limits = db.Column(JSON)
    eligibility_rules = db.Column(JSON)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('odds_configuration')
    def validate_odds_configuration(self, key, value):
        """Validate odds configuration format and total percentage"""
        if value is None:
            return value
            
        if isinstance(value, str):
            value = json.loads(value)
            
        if not isinstance(value, dict):
            raise ValueError("Odds configuration must be a dictionary")
            
        prizes = value.get('prizes', [])
        if not prizes:
            raise ValueError("Must include at least one prize configuration")
            
        # Validate total odds equal 100%
        total_odds = sum(prize.get('odds', 0) for prize in prizes)
        if total_odds != 100:
            raise ValueError("Total odds must equal 100%")
            
        # Validate each prize configuration
        for prize in prizes:
            if not all(k in prize for k in ('prize_id', 'odds', 'quantity')):
                raise ValueError("Each prize must have prize_id, odds, and quantity")
            if prize['odds'] <= 0 or prize['quantity'] <= 0:
                raise ValueError("Odds and quantity must be positive numbers")
                
        return value

    def lock_pool(self):
        """Lock the pool for use"""
        if self.status not in [PoolStatus.DRAFT.value, PoolStatus.ACTIVE.value]:
            raise ValueError(f"Cannot lock pool in {self.status} status")
            
        self.is_locked = True
        self.status = PoolStatus.LOCKED.value
        
        # Calculate and store totals
        if self.odds_configuration:
            prizes = self.odds_configuration.get('prizes', [])
            self.total_prizes = sum(p['quantity'] for p in prizes)
            self.available_prizes = self.total_prizes

    def unlock_pool(self, admin_id: int):
        """Unlock the pool (admin only)"""
        self.is_locked = False
        self.status = PoolStatus.ACTIVE.value

    def update_configuration(self, new_config: dict):
        """Update pool configuration"""
        if self.is_locked:
            raise ValueError("Cannot update locked pool")
            
        # Validate and update
        self.odds_configuration = new_config
        
        # Update totals
        prizes = new_config.get('prizes', [])
        self.total_prizes = sum(p['quantity'] for p in prizes)
        self.available_prizes = self.total_prizes

    def reserve_prize(self) -> tuple[int, float]:
        """
        Reserve a prize based on odds configuration
        Returns: (prize_id, prize_value)
        """
        if not self.is_locked:
            raise ValueError("Pool must be locked before reserving prizes")
            
        if self.available_prizes <= 0:
            raise ValueError("No prizes available")
            
        # Prize selection logic will be implemented in Phase 2
        raise NotImplementedError("Prize reservation to be implemented in Phase 2")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'is_locked': self.is_locked,
            'allocation_strategy': self.allocation_strategy,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'odds_configuration': self.odds_configuration,
            'total_prizes': self.total_prizes,
            'available_prizes': self.available_prizes,
            'budget_limit': float(self.budget_limit) if self.budget_limit else None,
            'current_allocation': float(self.current_allocation),
            'total_value': float(self.total_value) if self.total_value else 0,
            'allocation_rules': self.allocation_rules,
            'win_limits': self.win_limits,
            'eligibility_rules': self.eligibility_rules,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }