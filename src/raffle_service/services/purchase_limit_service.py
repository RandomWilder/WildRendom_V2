from typing import Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from src.shared import db
from flask import current_app
from src.raffle_service.models import UserRaffleStats, Raffle

class PurchaseLimitService:
    @staticmethod
    def check_purchase_limit(user_id: int, raffle_id: int, requested_quantity: int, max_tickets: int = None) -> Tuple[bool, Optional[str]]:
        """
        Check if a purchase would exceed the user's limit
        Returns: (allowed: bool, error_message: Optional[str])
        """
        try:
            # Get raffle to check its specific limits
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return False, "Raffle not found"

            # First check transaction size limit
            if requested_quantity > current_app.config['RAFFLE'].MAX_TICKETS_PER_TRANSACTION:
                return False, f"Maximum purchase is {current_app.config['RAFFLE'].MAX_TICKETS_PER_TRANSACTION} tickets per transaction"

            # Get or create user stats for this raffle
            stats = UserRaffleStats.query.filter_by(
                user_id=user_id,
                raffle_id=raffle_id
            ).first()

            if not stats:
                stats = UserRaffleStats(
                    user_id=user_id,
                    raffle_id=raffle_id,
                    tickets_purchased=0
                )
                db.session.add(stats)
                db.session.commit()

            # Check if purchase would exceed raffle-specific limit
            total_tickets = stats.tickets_purchased + requested_quantity
            if total_tickets > raffle.max_tickets_per_user:
                return False, f"Purchase would exceed limit of {raffle.max_tickets_per_user} tickets per user for this raffle. You currently have {stats.tickets_purchased} tickets."

            return True, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Database error: {str(e)}"

    @staticmethod
    def get_user_stats(user_id: int, raffle_id: int) -> Tuple[Optional[UserRaffleStats], Optional[str]]:
        """Get user's stats for a specific raffle"""
        try:
            stats = UserRaffleStats.query.filter_by(
                user_id=user_id,
                raffle_id=raffle_id
            ).first()
            return stats, None
        except SQLAlchemyError as e:
            return None, str(e)
        
    @staticmethod
    def update_purchase_count(user_id: int, raffle_id: int, quantity: int) -> Tuple[bool, Optional[str]]:
        """Update the user's purchase count after a successful ticket purchase"""
        try:
            stats = UserRaffleStats.query.filter_by(
                user_id=user_id,
                raffle_id=raffle_id
            ).first()

            if not stats:
                stats = UserRaffleStats(
                    user_id=user_id,
                    raffle_id=raffle_id,
                    tickets_purchased=0
                )
                db.session.add(stats)

            stats.tickets_purchased += quantity
            stats.last_purchase_time = datetime.now(timezone.utc)
            
            db.session.commit()
            return True, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)