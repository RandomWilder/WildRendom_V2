# src/prize_service/models/relationships.py

from src.shared import db
from .prize import Prize
from .prize_pool import PrizePool
from .prize_allocation import PrizeAllocation, PrizePoolAllocation

# Prize Pool to Prize relationship through PrizePoolAllocation
PrizePool.prizes = db.relationship('Prize',
    secondary='prize_pool_allocations',
    backref=db.backref('pools', lazy=True),
    lazy='dynamic'
)

# Prize Allocation relationships
Prize.allocations = db.relationship('PrizeAllocation',
    backref=db.backref('prize', lazy=True),
    lazy='dynamic'
)

PrizePool.allocations = db.relationship('PrizeAllocation',
    backref=db.backref('pool', lazy=True),
    lazy='dynamic'
)

# Add to models/__init__.py for easy imports
from .prize import Prize, PrizeType, PrizeStatus, PrizeTier
from .prize_pool import PrizePool, PoolStatus, AllocationStrategy
from .prize_allocation import PrizeAllocation, PrizePoolAllocation, AllocationType, ClaimStatus
from . import relationships

__all__ = [
    'Prize', 'PrizeType', 'PrizeStatus', 'PrizeTier',
    'PrizePool', 'PoolStatus', 'AllocationStrategy',
    'PrizeAllocation', 'PrizePoolAllocation', 'AllocationType', 'ClaimStatus'
]