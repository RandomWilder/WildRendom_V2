# src/prize_service/services/claim_service.py

from typing import Optional, Tuple, Dict, List  
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_
from src.shared import db
from src.prize_service.models import Prize, PrizeAllocation, ClaimStatus, AllocationType
from src.user_service.services.user_service import UserService
import logging

logger = logging.getLogger(__name__)

class ClaimService:
    @staticmethod
    def initiate_claim(
        allocation_id: int,
        user_id: int,
        claim_method: str = 'credit'
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Initiate a prize claim with instance management"""
        try:
            # Get allocation with locking
            allocation = db.session.query(PrizeAllocation).with_for_update().get(allocation_id)
            if not allocation:
                return None, "Prize allocation not found"

            # Verify ownership
            if allocation.winner_user_id != user_id:
                return None, "Not authorized to claim this prize"

            # Verify allocation status
            if allocation.claim_status != ClaimStatus.PENDING.value:
                return None, f"Cannot claim prize in {allocation.claim_status} status"

            # Check expiry
            current_time = datetime.now(timezone.utc)
            if allocation.claim_deadline and current_time > allocation.claim_deadline:
                allocation.claim_status = ClaimStatus.EXPIRED.value
                db.session.commit()
                return None, "Prize claim has expired"

            # Get prize details
            prize = Prize.query.get(allocation.prize_id)
            if not prize:
                return None, "Prize configuration not found"

            # Verify claim method
            if claim_method != prize.claim_processor_type:
                return None, f"Invalid claim method. Must use: {prize.claim_processor_type}"

            # Update allocation status
            allocation.claim_method = claim_method

            # Process based on claim method
            if claim_method == 'credit':
                return ClaimService._process_credit_claim(allocation, prize, user_id)
            elif claim_method == 'digital':
                # Placeholder for future digital prize delivery
                return None, "Digital prize claims not yet implemented"
            elif claim_method == 'cash':
                # Placeholder for future cash prize processing
                return None, "Cash prize claims not yet implemented"
            else:
                return None, "Unsupported claim method"

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in initiate_claim: {str(e)}")
            return None, str(e)

    @staticmethod
    def _process_credit_claim(
        allocation: PrizeAllocation,
        prize: Prize,
        user_id: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Process a credit-based prize claim with instance update"""
        try:
            # Verify instance is still valid
            if allocation.instance_identifier:
                pool = allocation.pool
                if pool and pool.odds_configuration:
                    instance_found = False
                    for prize_config in pool.odds_configuration.get('prizes', []):
                        for instance in prize_config.get('instances', []):
                            if instance.get('instance_id') == allocation.instance_identifier:
                                if instance.get('status') != 'allocated':
                                    return None, "Prize instance no longer available"
                                instance_found = True
                                instance['status'] = 'claimed'
                                break
                        if instance_found:
                            break
                    if not instance_found:
                        return None, "Prize instance not found"

            credit_amount = float(prize.credit_value)

            # Award credits to user
            user, error = UserService.update_credits(
                user_id=user_id,
                amount=credit_amount,
                transaction_type='add',
                reference_type='prize_claim',
                reference_id=str(allocation.id),
                notes=f'Prize claim: {prize.name}'
            )

            if error:
                return None, f"Failed to award credits: {error}"

            # Update allocation
            allocation.claim_status = ClaimStatus.CLAIMED.value
            allocation.claimed_at = datetime.now(timezone.utc)
            allocation.value_claimed = credit_amount

            # Update prize stats
            prize.total_claimed += 1

            db.session.commit()

            return {
                'allocation_id': allocation.id,
                'prize_id': prize.id,
                'prize_name': prize.name,
                'instance_id': allocation.instance_identifier,
                'credits_awarded': credit_amount,
                'claimed_at': allocation.claimed_at.isoformat()
            }, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in _process_credit_claim: {str(e)}")
            return None, str(e)

    @staticmethod
    def check_claim_status(
        allocation_id: int,
        user_id: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Check status of a prize claim with instance information"""
        try:
            allocation = PrizeAllocation.query.get(allocation_id)
            if not allocation:
                return None, "Prize allocation not found"

            if allocation.winner_user_id != user_id:
                return None, "Not authorized to view this claim"

            prize = Prize.query.get(allocation.prize_id)
            if not prize:
                return None, "Prize not found"

            return {
                'allocation_id': allocation.id,
                'status': allocation.claim_status,
                'claim_deadline': allocation.claim_deadline.isoformat() if allocation.claim_deadline else None,
                'claimed_at': allocation.claimed_at.isoformat() if allocation.claimed_at else None,
                'claim_method': allocation.claim_method,
                'value_claimed': float(allocation.value_claimed) if allocation.value_claimed else None,
                'prize_name': prize.name,
                'prize_type': prize.type,
                'instance_id': allocation.instance_identifier,
                'allowed_claim_methods': [prize.claim_processor_type]
            }, None

        except SQLAlchemyError as e:
            logger.error(f"Database error in check_claim_status: {str(e)}")
            return None, str(e)

    @staticmethod
    def expire_stale_claims() -> Tuple[int, Optional[str]]:
        """Expire unclaimed prizes and update instance statuses"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Find pending claims past deadline
            expired = PrizeAllocation.query.filter(
                and_(
                    PrizeAllocation.claim_status == ClaimStatus.PENDING.value,
                    PrizeAllocation.claim_deadline < current_time
                )
            ).all()

            expire_count = 0
            for allocation in expired:
                allocation.claim_status = ClaimStatus.EXPIRED.value
                
                # Update instance status if applicable
                if allocation.instance_identifier and allocation.pool:
                    pool = allocation.pool
                    if pool.odds_configuration:
                        for prize in pool.odds_configuration.get('prizes', []):
                            for instance in prize.get('instances', []):
                                if instance.get('instance_id') == allocation.instance_identifier:
                                    instance['status'] = 'expired'
                                    break

                expire_count += 1
                logger.info(
                    f"Expired allocation {allocation.id} for prize {allocation.prize_id}"
                    f" won by user {allocation.winner_user_id}"
                )

            db.session.commit()
            return expire_count, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in expire_stale_claims: {str(e)}")
            return 0, str(e)

    @staticmethod
    def get_expired_claims(
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Tuple[Optional[List[PrizeAllocation]], Optional[str]]:
        """Get list of expired claims with instance data for reporting"""
        try:
            query = PrizeAllocation.query.filter_by(claim_status=ClaimStatus.EXPIRED.value)

            if start_date:
                query = query.filter(PrizeAllocation.claim_deadline >= start_date)
            if end_date:
                query = query.filter(PrizeAllocation.claim_deadline <= end_date)

            expired_claims = query.order_by(PrizeAllocation.claim_deadline.desc()).all()
            return expired_claims, None

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_expired_claims: {str(e)}")
            return None, str(e)