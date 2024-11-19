# src/user_service/services/tier_service.py

from typing import Optional, Tuple, Dict, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
from src.shared import db
from src.user_service.models.user_tier import UserTier, UserTierHistory, TierLevel
from src.user_service.services.activity_service import ActivityService
import logging

logger = logging.getLogger(__name__)

class TierService:
    @staticmethod
    def get_user_tier(user_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Get user's current tier and benefits"""
        try:
            tier = UserTier.query.filter_by(user_id=user_id).first()
            if not tier:
                return None, "User tier not found"
                
            return tier.to_dict(), None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_user_tier: {str(e)}")
            return None, str(e)

    @staticmethod
    def evaluate_user_tier(user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Evaluate and potentially update user's tier based on activity
        Returns: (changed: bool, error: Optional[str])
        """
        try:
            tier = UserTier.query.filter_by(user_id=user_id).with_for_update().first()
            if not tier:
                return False, "User tier not found"

            # Record old tier for comparison
            old_tier = tier.current_tier
            
            # Update 90-day metrics
            TierService._update_rolling_metrics(tier)
            
            # Evaluate new tier
            tier_changed = tier.evaluate_tier()
            
            if tier_changed:
                # Log the change
                ActivityService.log_activity(
                    user_id=user_id,
                    activity_type='tier_change',
                    request=None,  # System-generated event
                    status='success',
                    details={
                        'previous_tier': old_tier,
                        'new_tier': tier.current_tier,
                        'metrics': {
                            'spend_90d': tier.spend_90d,
                            'participations_90d': tier.participations_90d,
                            'wins_90d': tier.wins_90d
                        }
                    }
                )
                
            db.session.commit()
            return tier_changed, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in evaluate_user_tier: {str(e)}")
            return False, str(e)

    @staticmethod
    def _update_rolling_metrics(tier: UserTier):
        """Update 90-day rolling metrics for tier evaluation"""
        try:
            ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
            
            # Get credit transactions for spend calculation
            from src.user_service.models import CreditTransaction
            spend = db.session.query(func.sum(CreditTransaction.amount))\
                .filter(
                    CreditTransaction.user_id == tier.user_id,
                    CreditTransaction.transaction_type == 'subtract',
                    CreditTransaction.created_at >= ninety_days_ago
                ).scalar() or 0.0
            
            # Get participation count
            from src.raffle_service.models import Ticket
            participations = Ticket.query\
                .filter(
                    Ticket.user_id == tier.user_id,
                    Ticket.status == 'sold',
                    Ticket.purchase_time >= ninety_days_ago
                ).count()

            # Get win count
            from src.prize_service.models import PrizeAllocation
            wins = PrizeAllocation.query\
                .filter(
                    PrizeAllocation.winner_user_id == tier.user_id,
                    PrizeAllocation.won_at >= ninety_days_ago,
                    PrizeAllocation.claim_status.in_(['claimed', 'pending'])
                ).count()

            # Update tier metrics
            tier.spend_90d = abs(float(spend))  # Convert to positive number
            tier.participations_90d = participations
            tier.wins_90d = wins
            
            # Update total metrics
            tier.total_spent += abs(float(spend))
            tier.total_participations += participations
            tier.total_wins += wins
            
            tier.last_activity_date = datetime.now(timezone.utc)

        except SQLAlchemyError as e:
            logger.error(f"Error updating rolling metrics: {str(e)}")
            raise

    @staticmethod
    def get_tier_progress(user_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Get user's progress towards next tier"""
        try:
            tier = UserTier.query.filter_by(user_id=user_id).first()
            if not tier:
                return None, "User tier not found"

            current_level = TierLevel(tier.current_tier)
            next_requirements = {
                TierLevel.BRONZE: {
                    'next_tier': 'SILVER',
                    'spend_required': 100,
                    'participations_required': 5,
                    'wins_required': 0
                },
                TierLevel.SILVER: {
                    'next_tier': 'GOLD',
                    'spend_required': 500,
                    'participations_required': 15,
                    'wins_required': 1
                },
                TierLevel.GOLD: {
                    'next_tier': 'PLATINUM',
                    'spend_required': 2000,
                    'participations_required': 30,
                    'wins_required': 2
                },
                TierLevel.PLATINUM: {
                    'next_tier': None,
                    'spend_required': None,
                    'participations_required': None,
                    'wins_required': None
                }
            }

            reqs = next_requirements[current_level]
            if not reqs['next_tier']:
                return {
                    'current_tier': tier.current_tier,
                    'message': "Maximum tier reached",
                    'progress': None
                }, None

            progress = {
                'current_tier': tier.current_tier,
                'next_tier': reqs['next_tier'],
                'metrics': {
                    'spend': {
                        'current': tier.spend_90d,
                        'required': reqs['spend_required'],
                        'percentage': min(100, (tier.spend_90d / reqs['spend_required'] * 100))
                    },
                    'participations': {
                        'current': tier.participations_90d,
                        'required': reqs['participations_required'],
                        'percentage': min(100, (tier.participations_90d / reqs['participations_required'] * 100))
                    },
                    'wins': {
                        'current': tier.wins_90d,
                        'required': reqs['wins_required'],
                        'percentage': min(100, (tier.wins_90d / max(1, reqs['wins_required']) * 100))
                    }
                },
                'benefits': {
                    'current': {
                        'purchase_limit_multiplier': tier.purchase_limit_multiplier,
                        'early_access_hours': tier.early_access_hours,
                        'has_exclusive_access': tier.has_exclusive_access
                    },
                    'next': TierService.get_tier_benefits(reqs['next_tier'])
                }
            }

            return progress, None

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_tier_progress: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_tier_benefits(tier_level: str) -> Dict:
        """Get benefits for a specific tier level"""
        benefits = {
            'BRONZE': {
                'purchase_limit_multiplier': 1.0,
                'early_access_hours': 0,
                'has_exclusive_access': False
            },
            'SILVER': {
                'purchase_limit_multiplier': 1.1,
                'early_access_hours': 0,
                'has_exclusive_access': False
            },
            'GOLD': {
                'purchase_limit_multiplier': 1.25,
                'early_access_hours': 12,
                'has_exclusive_access': True
            },
            'PLATINUM': {
                'purchase_limit_multiplier': 1.5,
                'early_access_hours': 24,
                'has_exclusive_access': True
            }
        }
        return benefits.get(tier_level, benefits['BRONZE'])

    @staticmethod
    def get_tier_history(user_id: int) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Get user's tier change history"""
        try:
            tier = UserTier.query.filter_by(user_id=user_id).first()
            if not tier:
                return None, "User tier not found"

            history = UserTierHistory.query\
                .filter_by(user_tier_id=tier.id)\
                .order_by(UserTierHistory.changed_at.desc())\
                .all()

            return [h.to_dict() for h in history], None

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_tier_history: {str(e)}")
            return None, str(e)