# src/prize_service/services/claim_service.py

from typing import Optional, Tuple, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from src.shared import db
from src.prize_service.models import (
    Prize, PrizeAllocation, ClaimStatus, 
    PrizeStatus, AllocationType
)

class ClaimService:
    @staticmethod
    def initiate_claim(
        allocation_id: int,
        user_id: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Initiate the claim process for a prize"""
        try:
            allocation = PrizeAllocation.query.get(allocation_id)
            if not allocation:
                return None, "Prize allocation not found"
                
            if allocation.winner_user_id != user_id:
                return None, "Not authorized to claim this prize"
                
            if allocation.claim_status != ClaimStatus.PENDING.value:
                return None, f"Prize not claimable. Status: {allocation.claim_status}"

            prize = Prize.query.get(allocation.prize_id)
            if not prize:
                return None, "Prize not found"

            claim_info = {
                'allocation_id': allocation.id,
                'prize_name': prize.name,
                'prize_type': prize.type,
                'claim_options': {
                    'prize': float(prize.retail_value),
                    'cash': float(prize.cash_value),
                    'credit': float(prize.credit_value)
                },
                'claim_deadline': allocation.claim_deadline.isoformat()
            }
            
            return claim_info, None

        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def process_claim(
        allocation_id: int,
        user_id: int,
        claim_method: str
    ) -> Tuple[Optional[PrizeAllocation], Optional[str]]:
        """Process a claim choice and initiate fulfillment"""
        try:
            allocation = PrizeAllocation.query.get(allocation_id)
            if not allocation:
                return None, "Prize allocation not found"

            prize = Prize.query.get(allocation.prize_id)
            if not prize:
                return None, "Prize not found"

            # Validate claim method
            valid_methods = ['prize', 'cash', 'credit']
            if claim_method not in valid_methods:
                return None, f"Invalid claim method. Must be one of: {valid_methods}"

            # Update allocation with claim choice
            allocation.claim_method = claim_method
            allocation.claim_status = ClaimStatus.APPROVED.value
            allocation.value_claimed = getattr(prize, f'{claim_method}_value')
            allocation.claimed_at = datetime.now(timezone.utc)

            db.session.commit()

            # TODO: Trigger fulfillment process based on claim method
            # This will integrate with future fulfillment service

            return allocation, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def check_claim_status(
        allocation_id: int,
        user_id: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Check the status of a prize claim"""
        try:
            allocation = PrizeAllocation.query.get(allocation_id)
            if not allocation:
                return None, "Prize allocation not found"

            if allocation.winner_user_id != user_id:
                return None, "Not authorized to view this claim"

            status_info = {
                'status': allocation.claim_status,
                'claimed_at': allocation.claimed_at.isoformat() if allocation.claimed_at else None,
                'claim_method': allocation.claim_method,
                'value_claimed': float(allocation.value_claimed) if allocation.value_claimed else None,
                'deadline': allocation.claim_deadline.isoformat() if allocation.claim_deadline else None
            }

            return status_info, None

        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def expire_stale_claims() -> Tuple[int, Optional[str]]:
        """Expire claims that have passed their deadline"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_count = PrizeAllocation.query.filter(
                and_(
                    PrizeAllocation.claim_status == ClaimStatus.PENDING.value,
                    PrizeAllocation.claim_deadline < current_time
                )
            ).update({
                'claim_status': ClaimStatus.EXPIRED.value
            })

            db.session.commit()
            return expired_count, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return 0, str(e)