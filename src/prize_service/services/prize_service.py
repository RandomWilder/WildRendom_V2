# src/prize_service/services/prize_service.py

from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
from decimal import Decimal
from src.prize_service.services.credit_service import CreditService
from src.shared import db
from src.prize_service.models import (
    Prize, PrizePool, PrizeInstance,
    PrizeStatus, PoolStatus, InstanceStatus, PrizeType
)
import logging

logger = logging.getLogger(__name__)

class PrizeService:
    @staticmethod
    def create_prize(data: dict, admin_id: int) -> Tuple[Optional[Prize], Optional[str]]:
        """Create a new prize"""
        try:
            # Value validations first
            if Decimal(str(data.get('cash_value', 0))) > Decimal(str(data.get('retail_value', 0))):
                return None, "cash_value cannot exceed retail_value"
            
            if Decimal(str(data.get('credit_value', 0))) <= 0:
                return None, "credit_value must be positive"

            # Type validation
            if data.get('type') not in [t.value for t in PrizeType]:
                valid_types = [t.value for t in PrizeType]
                return None, f"Invalid prize type. Must be one of: {', '.join(valid_types)}"

            prize = Prize(
                name=data['name'],
                description=data.get('description'),
                type=data['type'],
                tier=data['tier'],
                retail_value=data['retail_value'],
                cash_value=data['cash_value'],
                credit_value=data['credit_value'],
                expiry_days=data.get('expiry_days', 7),
                created_by_id=admin_id,
                status=PrizeStatus.ACTIVE.value
            )

            db.session.add(prize)
            db.session.commit()
            
            logger.info(f"Created new prize {prize.id}: {prize.name}")
            return prize, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating prize: {str(e)}")
            return None, str(e)

    @staticmethod
    def update_prize(prize_id: int, data: dict, admin_id: int) -> Tuple[Optional[Prize], Optional[str]]:
        """Update prize template if not used in any pool"""
        try:
            prize = db.session.get(Prize, prize_id)
            if not prize:
                return None, "Prize not found"

            # Check if prize is used in any pool
            if PrizeInstance.query.filter_by(prize_id=prize_id).first():
                return None, "Cannot update prize that is used in pools"

            # Update allowed fields
            prize.name = data.get('name', prize.name)
            prize.retail_value = data.get('retail_value', prize.retail_value)
            prize.cash_value = data.get('cash_value', prize.cash_value)
            prize.credit_value = data.get('credit_value', prize.credit_value)
            
            # Validate values after update
            if Decimal(str(prize.cash_value)) > Decimal(str(prize.retail_value)):
                return None, "cash_value cannot exceed retail_value"
            
            if Decimal(str(prize.credit_value)) <= 0:
                return None, "credit_value must be positive"
            
            prize.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return prize, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating prize: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_prize(prize_id: int) -> Optional[Prize]:
        """Get prize by ID"""
        return db.session.get(Prize, prize_id)

    @staticmethod
    def list_prizes() -> List[Prize]:
        """Get all prizes"""
        return db.session.query(Prize).all()

    @staticmethod
    def create_pool(data: dict, admin_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Create a new prize pool"""
        try:
            pool = PrizePool(
                name=data['name'],
                description=data.get('description'),
                created_by_id=admin_id,
                status=PoolStatus.UNLOCKED.value
            )

            db.session.add(pool)
            db.session.commit()
            
            # Return the formatted response directly as a dict
            response = {
                'pool_id': pool.id,
                'name': pool.name,
                'description': pool.description,
                'total_instances': 0,
                'values': {
                    'retail_total': 0,
                    'cash_total': 0,
                    'credit_total': 0
                },
                'status': pool.status
            }
            
            logger.info(f"Created new pool {pool.id}: {pool.name}")
            return response, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating pool: {str(e)}")
            return None, str(e)

    @staticmethod
    def allocate_to_pool(pool_id: int, prize_id: int, quantity: int, collective_odds: float, admin_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Allocate prizes to pool"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            if pool.status != PoolStatus.UNLOCKED.value:
                return None, "Can only allocate to UNLOCKED pools"

            prize = db.session.get(Prize, prize_id)
            if not prize:
                return None, "Prize not found"

            # Calculate individual odds for each instance
            individual_odds = collective_odds / quantity

            # Find the last used sequence number for this pool-prize combination
            last_instance = db.session.query(PrizeInstance)\
                .filter(
                    PrizeInstance.pool_id == pool_id,
                    PrizeInstance.prize_id == prize_id
                )\
                .order_by(PrizeInstance.instance_id.desc())\
                .first()

            # Determine the starting sequence number
            start_seq = 1
            if last_instance:
                # Extract the last sequence number and increment
                last_seq = int(last_instance.instance_id.split('-')[2])
                start_seq = last_seq + 1

            # Create instances
            instances = []
            for i in range(quantity):
                # Generate sequence numbers continuing from the last used one
                seq_num = str(start_seq + i).zfill(3)
                instance_id = f"{pool_id}-{prize_id}-{seq_num}"
                
                instance = PrizeInstance(
                    instance_id=instance_id,
                    pool_id=pool_id,
                    prize_id=prize_id,
                    individual_odds=individual_odds,
                    status=InstanceStatus.AVAILABLE.value,
                    retail_value=prize.retail_value,
                    cash_value=prize.cash_value,
                    credit_value=prize.credit_value,
                    created_by_id=admin_id
                )
                db.session.add(instance)
                instances.append(instance)

            # Update pool counts
            pool.total_instances += quantity
            pool.available_instances += quantity
            if prize.type == 'Draw_Win':
                pool.draw_win_count += quantity
            else:
                pool.instant_win_count += quantity

            # Update pool value totals
            pool.retail_total += prize.retail_value * quantity
            pool.cash_total += prize.cash_value * quantity
            pool.credit_total += prize.credit_value * quantity

            # Commit all changes
            db.session.commit()
                
            # Return successful allocation result
            return {
                'allocated_instances': [inst.to_dict() for inst in instances],
                'pool_updated_totals': pool.to_dict()
            }, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error allocating prizes: {str(e)}")
            return None, str(e)

    @staticmethod
    def claim_prize(
        instance_id: int, 
        user_id: int,
        claim_method: str = 'credit'
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Process a prize claim with attempt tracking"""
        try:
            instance = PrizeInstance.query.get(instance_id)
            if not instance:
                return None, "Prize instance not found"

            if not instance.can_be_claimed():
                return None, "Prize cannot be claimed"

            # Increment claim attempt
            if not instance.increment_claim_attempt():
                return None, "Maximum claim attempts exceeded"

            # Process claim based on method
            if claim_method == 'credit':
                success = CreditService.process_prize_claim(
                    instance_id=instance_id,
                    user_id=user_id,
                    amount=float(instance.credit_value)
                )
                
                if not success:
                    return None, "Credit processing failed"

            # Update instance on successful claim
            instance.status = InstanceStatus.CLAIMED.value
            instance.claimed_by_id = user_id
            instance.claimed_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            return instance.to_dict(), None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error processing claim: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_user_prizes(user_id: int) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Get all prizes claimed by a user"""
        try:
            instances = PrizeInstance.query.filter_by(
                claimed_by_id=user_id,
                status=InstanceStatus.CLAIMED.value
            ).all()
            
            return [inst.to_dict() for inst in instances], None
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving user prizes: {str(e)}")
            return None, str(e)

    @staticmethod
    def process_expired_claims() -> Tuple[int, Optional[str]]:
        """Process expired claims and reset instances"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_count = 0

            # Find expired but unclaimed instances
            expired_instances = PrizeInstance.query.filter(
                and_(
                    PrizeInstance.status == InstanceStatus.DISCOVERED.value,
                    PrizeInstance.claim_deadline < current_time
                )
            ).all()

            for instance in expired_instances:
                instance.status = InstanceStatus.AVAILABLE.value
                instance.claim_attempts = 0
                expired_count += 1
                logger.info(f"Reset expired instance {instance.instance_id}")

            db.session.commit()
            
            if expired_count > 0:
                logger.info(f"Processed {expired_count} expired claims")
                
            return expired_count, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error processing expired claims: {str(e)}")
            return 0, str(e)

    @staticmethod
    def get_prize_values(instance_id: int) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
        """Get available value options for prize instance"""
        try:
            instance = PrizeInstance.query.get(instance_id)
            if not instance:
                return None, "Prize instance not found"

            return {
                'retail_value': float(instance.retail_value),
                'cash_value': float(instance.cash_value),
                'credit_value': float(instance.credit_value)
            }, None

        except SQLAlchemyError as e:
            logger.error(f"Error getting prize values: {str(e)}")
            return None, str(e)

    @staticmethod
    def validate_prize_selection(prize_id: int, selected_value: str) -> Tuple[bool, Optional[str]]:
        """Validate selected prize value option"""
        try:
            prize = Prize.query.get(prize_id)
            if not prize:
                return False, "Prize not found"

            valid_values = {
                'retail': float(prize.retail_value),
                'cash': float(prize.cash_value),
                'credit': float(prize.credit_value)
            }

            if selected_value not in valid_values:
                return False, "Invalid value selection"

            return True, None

        except SQLAlchemyError as e:
            logger.error(f"Error validating prize selection: {str(e)}")
            return False, str(e)

    # Pool management methods
    @staticmethod
    def lock_pool(pool_id: int, admin_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Lock prize pool with validation"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            if pool.status != PoolStatus.UNLOCKED.value:
                return None, "Can only lock UNLOCKED pools"

            # Run validations
            is_valid, error = pool.validate_for_lock()
            if not is_valid:
                return None, error

            # Lock pool
            pool.status = PoolStatus.LOCKED.value
            pool.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Successfully locked pool {pool_id}")
            return pool.to_dict(), None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error locking pool: {str(e)}")
            return None, str(e)

    @staticmethod
    def unlock_pool(pool_id: int, admin_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Unlock a locked pool if conditions allow"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            if pool.status != PoolStatus.LOCKED.value:
                return None, "Can only unlock LOCKED pools"

            if not pool.check_can_unlock():
                return None, "Cannot unlock pool - in use by active raffle"

            pool.status = PoolStatus.UNLOCKED.value
            pool.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Successfully unlocked pool {pool_id}")
            return pool.to_dict(), None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error unlocking pool: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_pool_stats(pool_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Get comprehensive pool statistics"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            stats = {
                'total_instances': pool.total_instances,
                'by_type': {
                    'instant_win': {
                        'total': pool.instant_win_count,
                        'available': PrizeInstance.query.filter_by(
                            pool_id=pool_id,
                            status=InstanceStatus.AVAILABLE.value
                        ).count(),
                        'discovered': PrizeInstance.query.filter_by(
                            pool_id=pool_id,
                            status=InstanceStatus.DISCOVERED.value
                        ).count(),
                        'claimed': PrizeInstance.query.filter_by(
                            pool_id=pool_id,
                            status=InstanceStatus.CLAIMED.value
                        ).count()
                    },
                    'draw_win': {
                        'total': pool.draw_win_count,
                        'available': pool.draw_win_count - PrizeInstance.query.filter_by(
                            pool_id=pool_id,
                            status=InstanceStatus.CLAIMED.value
                        ).count()
                    }
                },
                'values': {
                    'retail_total': float(pool.retail_total),
                    'cash_total': float(pool.cash_total),
                    'credit_total': float(pool.credit_total),
                    'claimed': {
                        'retail': float(sum(inst.retail_value for inst in pool.instances.filter_by(
                            status=InstanceStatus.CLAIMED.value
                        ))),
                        'cash': float(sum(inst.cash_value for inst in pool.instances.filter_by(
                            status=InstanceStatus.CLAIMED.value
                        ))),
                        'credit': float(sum(inst.credit_value for inst in pool.instances.filter_by(
                            status=InstanceStatus.CLAIMED.value
                        )))
                    }
                }
            }
            
            return stats, None

        except SQLAlchemyError as e:
            logger.error(f"Error getting pool stats: {str(e)}")
            return None, str(e)

    @staticmethod
    def mark_pool_used(pool_id: int, raffle_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Mark pool as USED when raffle becomes active"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            if pool.status != PoolStatus.LOCKED.value:
                return None, "Can only mark LOCKED pools as USED"

            if pool.raffle_id != raffle_id:
                return None, "Pool not assigned to this raffle"

            pool.status = PoolStatus.USED.value
            pool.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Marked pool {pool_id} as USED by raffle {raffle_id}")
            return pool.to_dict(), None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error marking pool as used: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_pool_claim_stats(pool_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Get detailed claim statistics for a pool"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            stats = {
                'total_instances': pool.total_instances,
                'by_type': {
                    'Instant_Win': {
                        'count': pool.instant_win_count,
                        'allocated': PrizeInstance.query.filter_by(
                            pool_id=pool_id,
                            status=InstanceStatus.AVAILABLE.value
                        ).count(),
                        'discovered': PrizeInstance.query.filter_by(
                            pool_id=pool_id,
                            status=InstanceStatus.DISCOVERED.value
                        ).count(),
                        'claimed': PrizeInstance.query.filter_by(
                            pool_id=pool_id,
                            status=InstanceStatus.CLAIMED.value
                        ).count(),
                        'forfeited': 0  # For future use
                    },
                    'Draw_Win': {
                        'count': pool.draw_win_count,
                        'allocated': 0,
                        'claimed': PrizeInstance.query.filter_by(
                            pool_id=pool_id,
                            status=InstanceStatus.CLAIMED.value
                        ).count(),
                        'forfeited': 0
                    }
                },
                'values_claimed': {
                    'retail_total': float(sum(inst.retail_value for inst in pool.instances.filter_by(
                        status=InstanceStatus.CLAIMED.value
                    ))),
                    'cash_total': float(sum(inst.cash_value for inst in pool.instances.filter_by(
                        status=InstanceStatus.CLAIMED.value
                    ))),
                    'credit_total': float(sum(inst.credit_value for inst in pool.instances.filter_by(
                        status=InstanceStatus.CLAIMED.value
                    )))
                }
            }

            return stats, None

        except Exception as e:
            logger.error(f"Error getting pool stats: {str(e)}")
            return None, str(e)

    @staticmethod
    def assign_pool_to_raffle(pool_id: int, raffle_id: int, admin_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Assign a pool to a raffle"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            if pool.status != PoolStatus.LOCKED.value:
                return None, "Can only assign LOCKED pools"

            if pool.raffle_id:
                return None, "Pool already assigned to a raffle"

            pool.raffle_id = raffle_id
            pool.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Assigned pool {pool_id} to raffle {raffle_id}")
            return pool.to_dict(), None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error assigning pool to raffle: {str(e)}")
            return None, str(e)