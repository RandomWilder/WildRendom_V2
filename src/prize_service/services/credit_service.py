# src/prize_service/services/credit_service.py

from typing import Optional, Tuple, Dict
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from src.shared import db
from src.user_service.models import User
from src.user_service.models.credit_transaction import CreditTransaction
from src.prize_service.models import PrizeAllocation, ClaimStatus
import logging

logger = logging.getLogger(__name__)

class CreditService:
    @staticmethod
    def process_prize_claim(
        allocation_id: int,
        user_id: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Process a prize claim and award credits"""
        try:
            with db.session.begin_nested():
                # Get allocation with locking
                allocation = PrizeAllocation.query.with_for_update().get(allocation_id)
                if not allocation:
                    return None, "Prize allocation not found"

                # Verify ownership and status
                if allocation.winner_user_id != user_id:
                    return None, "Not authorized to claim this prize"
                    
                if allocation.claim_status != ClaimStatus.PENDING.value:
                    return None, f"Invalid claim status: {allocation.claim_status}"

                # Get user with locking
                user = User.query.with_for_update().get(user_id)
                if not user:
                    return None, "User not found"

                # Create credit transaction
                credit_amount = allocation.original_value
                transaction = CreditTransaction(
                    user_id=user_id,
                    amount=credit_amount,
                    transaction_type='add',
                    balance_after=user.site_credits + credit_amount,
                    reference_type='prize_claim',
                    reference_id=str(allocation_id),
                    notes=f"Prize claim credit award - Prize ID: {allocation.prize_id}",
                    created_by_id=user_id  # Self-initiated transaction
                )

                # Update user's credits
                user.site_credits += credit_amount

                # Update allocation status
                allocation.claim_status = ClaimStatus.CLAIMED.value
                allocation.claimed_at = datetime.now(timezone.utc)
                allocation.value_claimed = credit_amount

                # Add transaction
                db.session.add(transaction)

            # Commit outer transaction
            db.session.commit()

            logger.info(
                f"Processed prize claim {allocation_id} for user {user_id}. "
                f"Awarded {credit_amount} credits"
            )

            return {
                'transaction_id': transaction.id,
                'amount_awarded': credit_amount,
                'new_balance': user.site_credits,
                'claim_timestamp': allocation.claimed_at.isoformat()
            }, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in process_prize_claim: {str(e)}")
            return None, str(e)

    @staticmethod
    def verify_claim_eligibility(
        allocation_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Verify if a prize claim is eligible for credit award"""
        try:
            allocation = PrizeAllocation.query.get(allocation_id)
            if not allocation:
                return False, "Prize allocation not found"

            if allocation.winner_user_id != user_id:
                return False, "Not authorized to claim this prize"

            if allocation.claim_status != ClaimStatus.PENDING.value:
                return False, f"Invalid claim status: {allocation.claim_status}"

            if allocation.claim_deadline < datetime.now(timezone.utc):
                return False, "Claim deadline has passed"

            return True, None

        except SQLAlchemyError as e:
            logger.error(f"Database error in verify_claim_eligibility: {str(e)}")
            return False, str(e)

    @staticmethod
    def get_claim_statistics(allocation_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Get detailed statistics for a prize claim"""
        try:
            allocation = PrizeAllocation.query.get(allocation_id)
            if not allocation:
                return None, "Prize allocation not found"

            # Get related credit transaction if claimed
            transaction = None
            if allocation.claim_status == ClaimStatus.CLAIMED.value:
                transaction = CreditTransaction.query.filter_by(
                    reference_type='prize_claim',
                    reference_id=str(allocation_id)
                ).first()

            return {
                'allocation_id': allocation.id,
                'status': allocation.claim_status,
                'original_value': float(allocation.original_value),
                'claimed_value': float(allocation.value_claimed) if allocation.value_claimed else None,
                'claim_deadline': allocation.claim_deadline.isoformat(),
                'claimed_at': allocation.claimed_at.isoformat() if allocation.claimed_at else None,
                'transaction_id': transaction.id if transaction else None
            }, None

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_claim_statistics: {str(e)}")
            return None, str(e)