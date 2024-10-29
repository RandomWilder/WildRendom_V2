# src/prize_service/services/prize_service.py

from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_
from src.shared import db
from src.prize_service.models import (
    Prize, PrizePool, PrizeAllocation, PrizePoolAllocation,
    PrizeStatus, AllocationType, ClaimStatus
)

class PrizeService:
    @staticmethod
    def allocate_instant_win(
        pool_id: int,
        ticket_id: str,
        user_id: int
    ) -> Tuple[Optional[PrizeAllocation], Optional[str]]:
        """Allocate a prize for an instant win"""
        try:
            pool = PrizePool.query.get(pool_id)
            if not pool or not pool.is_active():
                return None, "Invalid or inactive prize pool"

            # Get available prizes in pool
            pool_prizes = PrizePoolAllocation.query.filter(
                and_(
                    PrizePoolAllocation.pool_id == pool_id,
                    PrizePoolAllocation.quantity_remaining > 0
                )
            ).all()

            if not pool_prizes:
                return None, "No prizes available in pool"

            # For now, select first available prize
            # TODO: Implement prize selection strategy based on rules
            selected_pool_prize = pool_prizes[0]
            prize = Prize.query.get(selected_pool_prize.prize_id)

            # Create allocation
            allocation = PrizeAllocation(
                prize_id=prize.id,
                pool_id=pool_id,
                allocation_type=AllocationType.INSTANT_WIN.value,
                reference_type='ticket',
                reference_id=ticket_id,
                winner_user_id=user_id,
                won_at=datetime.now(timezone.utc),
                claim_status=ClaimStatus.PENDING.value,
                claim_deadline=datetime.now(timezone.utc) + timedelta(days=1)
            )

            # Update quantities
            selected_pool_prize.quantity_remaining -= 1
            prize.available_quantity -= 1
            prize.total_won += 1

            db.session.add(allocation)
            db.session.commit()

            return allocation, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def allocate_raffle_prize(
        pool_id: int,
        raffle_id: str,
        user_id: int
    ) -> Tuple[Optional[PrizeAllocation], Optional[str]]:
        """Allocate a prize for a raffle win"""
        try:
            # Similar to instant win allocation but for raffle prizes
            # Implementation follows same pattern but with raffle-specific logic
            # TODO: Implement raffle prize allocation logic
            pass

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def claim_prize(
        allocation_id: int,
        user_id: int,
        claim_method: str
    ) -> Tuple[Optional[PrizeAllocation], Optional[str]]:
        """Process a prize claim"""
        try:
            allocation = PrizeAllocation.query.get(allocation_id)
            if not allocation:
                return None, "Prize allocation not found"

            if allocation.winner_user_id != user_id:
                return None, "Not authorized to claim this prize"

            if allocation.claim_status != ClaimStatus.PENDING.value:
                return None, f"Prize cannot be claimed. Status: {allocation.claim_status}"

            if allocation.claim_deadline and allocation.claim_deadline < datetime.now(timezone.utc):
                allocation.claim_status = ClaimStatus.EXPIRED.value
                db.session.commit()
                return None, "Prize claim has expired"

            # Process claim based on method
            prize = Prize.query.get(allocation.prize_id)
            if claim_method == 'cash':
                allocation.value_claimed = prize.cash_value
            elif claim_method == 'credit':
                allocation.value_claimed = prize.credit_value
            else:
                allocation.value_claimed = prize.retail_value

            allocation.claim_status = ClaimStatus.CLAIMED.value
            allocation.claimed_at = datetime.now(timezone.utc)
            allocation.claim_method = claim_method

            prize.total_claimed += 1
            
            db.session.commit()
            return allocation, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_user_prizes(user_id: int) -> Tuple[Optional[List[PrizeAllocation]], Optional[str]]:
        """Get all prizes won by a user"""
        try:
            allocations = PrizeAllocation.query.filter_by(winner_user_id=user_id).all()
            return allocations, None
        except SQLAlchemyError as e:
            return None, str(e)
        
    @staticmethod
    def create_prize(data: dict, admin_id: int) -> Tuple[Optional[Prize], Optional[str]]:
        """Create a new prize"""
        try:
            prize = Prize(
                name=data['name'],
                description=data.get('description'),
                type=data['type'],
                custom_type=data.get('custom_type'),
                tier=data.get('tier', 'silver'),
                retail_value=data['retail_value'],
                cash_value=data['cash_value'],
                credit_value=data['credit_value'],
                total_quantity=data.get('total_quantity'),
                available_quantity=data.get('total_quantity'),  # Initially same as total
                min_threshold=data.get('min_threshold', 0),
                win_limit_per_user=data.get('win_limit_per_user'),
                win_limit_period_days=data.get('win_limit_period_days'),
                status=PrizeStatus.ACTIVE.value,
                created_by_id=admin_id
            )

            db.session.add(prize)
            db.session.commit()
            return prize, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def create_pool(data: dict, admin_id: int) -> Tuple[Optional[PrizePool], Optional[str]]:
        """Create a new prize pool"""
        try:
            pool = PrizePool(
                name=data['name'],
                description=data.get('description'),
                start_date=data['start_date'],
                end_date=data['end_date'],
                budget_limit=data.get('budget_limit'),
                allocation_rules=data.get('allocation_rules'),
                win_limits=data.get('win_limits'),
                eligibility_rules=data.get('eligibility_rules'),
                created_by_id=admin_id
            )

            db.session.add(pool)
            db.session.commit()
            return pool, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def create_pool_allocation(pool_id: int, data: dict, admin_id: int) -> Tuple[Optional[PrizePoolAllocation], Optional[str]]:
        """Create a new prize pool allocation"""
        try:
            # Verify pool exists
            pool = PrizePool.query.get(pool_id)
            if not pool:
                return None, "Prize pool not found"

            # Verify prize exists
            prize = Prize.query.get(data['prize_id'])
            if not prize:
                return None, "Prize not found"

            # Create allocation
            allocation = PrizePoolAllocation(
                pool_id=pool_id,
                prize_id=data['prize_id'],
                quantity_allocated=data['quantity'],
                quantity_remaining=data['quantity'],
                allocation_rules=data.get('allocation_rules')
            )

            db.session.add(allocation)
            db.session.commit()
            return allocation, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)