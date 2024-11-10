# src/prize_service/models/relationships.py

from src.shared import db
from .prize import Prize
from .prize_pool import PrizePool
from .prize_allocation import PrizeAllocation

# Prize Pool to Prize relationship (many-to-many through allocations)
PrizePool.prizes = db.relationship(
    'Prize',
    secondary='prize_allocations',
    back_populates='pools',
    overlaps="allocations",
    lazy='dynamic'
)

Prize.pools = db.relationship(
    'PrizePool',
    secondary='prize_allocations',
    back_populates='prizes',
    overlaps="prize",
    lazy='dynamic'
)

# Prize Allocation relationships
Prize.allocations = db.relationship(
    'PrizeAllocation',
    back_populates='prize',
    overlaps="pools",
    lazy='dynamic'
)

PrizePool.allocations = db.relationship(
    'PrizeAllocation',
    back_populates='pool',
    overlaps="pools,prizes",
    lazy='dynamic'
)

# Set up bidirectional relationships with proper overlaps
PrizeAllocation.prize = db.relationship(
    'Prize',
    back_populates='allocations',
    overlaps="pools,prizes",  # Added 'prizes' to handle the warning
    lazy='joined'  # Using joined loading for better performance
)

PrizeAllocation.pool = db.relationship(
    'PrizePool',
    back_populates='allocations',
    overlaps="pools,prizes",
    lazy='joined'  # Using joined loading for better performance
)