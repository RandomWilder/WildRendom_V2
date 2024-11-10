# src/raffle_service/services/ticket_service.py

from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func, distinct
from flask import current_app
from src.shared import db
from src.raffle_service.models import Ticket, TicketStatus, Raffle, RaffleStatus
from src.raffle_service.services.purchase_limit_service import PurchaseLimitService
from src.raffle_service.services.instant_win_service import InstantWinService 
import logging
logger = logging.getLogger(__name__)
from src.raffle_service.models import (
    Ticket, TicketStatus, 
    Raffle, RaffleStatus,
    UserRaffleStats
)

class TicketService:
    @staticmethod
    def get_user_tickets(user_id: int, raffle_id: Optional[int] = None) -> Tuple[Optional[List[Ticket]], Optional[str]]:
        """Get all tickets owned by a user, optionally filtered by raffle"""
        try:
            query = Ticket.query.filter_by(user_id=user_id)
            if raffle_id:
                query = query.filter_by(raffle_id=raffle_id)
            
            tickets = query.all()
            return tickets, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def get_ticket_by_number(raffle_id: int, ticket_number: str) -> Tuple[Optional[Ticket], Optional[str]]:
        """Get specific ticket by its number"""
        try:
            ticket = Ticket.query.filter_by(
                raffle_id=raffle_id,
                ticket_number=ticket_number
            ).first()
            
            if not ticket:
                return None, "Ticket not found"
                
            return ticket, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def void_ticket(ticket_id: int, admin_id: int, reason: str) -> Tuple[Optional[Ticket], Optional[str]]:
        """Void a ticket (admin only)"""
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                return None, "Ticket not found"
                
            # Check if ticket can be voided
            if ticket.status == TicketStatus.VOID.value:
                return None, "Ticket is already void"
                
            if ticket.raffle.status in [RaffleStatus.ENDED.value, RaffleStatus.CANCELLED.value]:
                return None, "Cannot void ticket for ended or cancelled raffle"

            # Void the ticket
            ticket.status = TicketStatus.VOID.value
            
            # Record the action (we'll implement activity logging later)
            db.session.commit()
            
            return ticket, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def bulk_cancel_tickets(raffle_id: int) -> Tuple[Optional[int], Optional[str]]:
        """Cancel all unsold tickets for a raffle"""
        try:
            result = Ticket.query.filter(
                and_(
                    Ticket.raffle_id == raffle_id,
                    Ticket.status == TicketStatus.AVAILABLE.value
                )
            ).update({
                'status': TicketStatus.CANCELLED.value
            }, synchronize_session=False)
            
            db.session.commit()
            return result, None  # Returns number of tickets cancelled
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def purchase_tickets(user_id: int, raffle_id: int, quantity: int, transaction_id: int = None) -> Tuple[Optional[List[Ticket]], Optional[str]]:
        """Purchase tickets for a raffle with proper transaction management"""
        try:
            # Start an outer transaction
            with db.session.begin_nested():
                # 1. Check purchase limit first (moved from routes)
                allowed, error = PurchaseLimitService.check_purchase_limit(
                    user_id=user_id,
                    raffle_id=raffle_id,
                    requested_quantity=quantity
                )
                if not allowed:
                    return None, error

                # 2. Get available tickets with locking
                available_tickets = Ticket.query.filter_by(
                    raffle_id=raffle_id,
                    status=TicketStatus.AVAILABLE.value
                ).with_for_update().order_by(func.random()).limit(quantity).all()

                if len(available_tickets) < quantity:
                    return None, "Not enough tickets available"

                # 3. Update tickets
                purchase_time = datetime.now(timezone.utc)
                purchased_tickets = []

                for ticket in available_tickets:
                    ticket.user_id = user_id
                    ticket.status = TicketStatus.SOLD.value
                    ticket.purchase_time = purchase_time
                    ticket.transaction_id = transaction_id
                    purchased_tickets.append(ticket)

                # 4. Update purchase count only after we know we have the tickets
                success, error = PurchaseLimitService.update_purchase_count(
                    user_id=user_id,
                    raffle_id=raffle_id,
                    quantity=quantity
                )
                
                if not success:
                    # This will trigger rollback of the nested transaction
                    raise SQLAlchemyError(f"Failed to update purchase count: {error}")

                # 5. Verify final state
                final_count = sum(1 for t in Ticket.query.filter_by(
                    raffle_id=raffle_id,
                    user_id=user_id,
                    status=TicketStatus.SOLD.value
                ).all())

                stats = UserRaffleStats.query.filter_by(
                    user_id=user_id,
                    raffle_id=raffle_id
                ).first()

                if stats.tickets_purchased != final_count:
                    raise SQLAlchemyError(
                        f"Purchase count mismatch. Stats: {stats.tickets_purchased}, "
                        f"Actual: {final_count}"
                    )

            # Outer transaction commits here if everything succeeded
            db.session.commit()
            
            logger.info(
                f"Successfully purchased {quantity} tickets for user {user_id} "
                f"in raffle {raffle_id}. Transaction ID: {transaction_id}"
            )
            
            return purchased_tickets, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(
                f"Failed to purchase tickets: {str(e)}. "
                f"User: {user_id}, Raffle: {raffle_id}, Quantity: {quantity}"
            )
            return None, f"Failed to complete purchase: {str(e)}"

    @staticmethod
    def reveal_tickets(user_id: int, ticket_ids: List[str]) -> Tuple[Optional[List[Ticket]], Optional[str]]:
        """Reveal multiple tickets for a user"""
        try:
            # Get tickets and verify ownership in one query
            tickets = Ticket.query.filter(
                Ticket.ticket_id.in_(ticket_ids),
                Ticket.user_id == user_id,
                Ticket.status == TicketStatus.SOLD.value,
                Ticket.is_revealed == False
            ).order_by(Ticket.ticket_id).with_for_update().all()

            if not tickets:
                return None, "No eligible tickets found"

            # Get current highest reveal sequence for this raffle
            max_sequence = db.session.query(func.max(Ticket.reveal_sequence))\
                .filter(Ticket.raffle_id == tickets[0].raffle_id)\
                .scalar() or 0

            revealed_tickets = []
            instant_wins_found = []

            for i, ticket in enumerate(tickets, start=1):
                if ticket.reveal():
                    ticket.reveal_sequence = max_sequence + i
                    revealed_tickets.append(ticket)
                    
                    # Check for instant wins only during reveal
                    if ticket.instant_win_eligible and ticket.instant_win:
                        instant_win, error = InstantWinService.check_instant_win(ticket.id)
                        if instant_win and not error:
                            instant_wins_found.append(instant_win)

            db.session.commit()
            return revealed_tickets, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_revealed_tickets(user_id: int, raffle_id: int) -> Tuple[Optional[List[Ticket]], Optional[str]]:
        """Get all revealed tickets for a user in a raffle"""
        try:
            tickets = Ticket.query.filter(
                Ticket.raffle_id == raffle_id,
                Ticket.user_id == user_id,
                Ticket.is_revealed == True
            ).order_by(Ticket.reveal_sequence).all()

            return tickets, None

        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def mark_instant_win_eligible(raffle_id: int, count: int) -> Tuple[Optional[List[Ticket]], Optional[str]]:
        """Mark tickets as instant win eligible during raffle setup"""
        try:
            # Get random available tickets
            eligible_tickets = Ticket.query.filter(
                Ticket.raffle_id == raffle_id,
                Ticket.status == TicketStatus.AVAILABLE.value,
                Ticket.instant_win_eligible == False
            ).order_by(func.random()).limit(count).all()

            if len(eligible_tickets) < count:
                return None, f"Not enough available tickets. Found {len(eligible_tickets)}, needed {count}"

            for ticket in eligible_tickets:
                ticket.mark_instant_win_eligible()

            db.session.commit()
            return eligible_tickets, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_raffle_statistics(raffle_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Get ticket statistics for a raffle"""
        try:
            stats = {
                'total_tickets': 0,
                'available_tickets': 0,
                'sold_tickets': 0,
                'revealed_tickets': 0,
                'eligible_tickets': 0,
                'instant_wins_found': 0,
                'void_tickets': 0,
                'cancelled_tickets': 0,
                'total_sales': 0.0,
                'unique_participants': 0,
                'tickets_available_for_sale': 0
            }
            
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"

            # Get tickets with all states
            tickets = Ticket.query.filter_by(raffle_id=raffle_id).all()
            
            # Get unique participants count
            unique_participants = db.session.query(func.count(distinct(Ticket.user_id)))\
                .filter(
                    Ticket.raffle_id == raffle_id,
                    Ticket.user_id.isnot(None)
                ).scalar()
            
            stats['unique_participants'] = unique_participants or 0
            
            for ticket in tickets:
                stats['total_tickets'] += 1
                
                if ticket.status == TicketStatus.AVAILABLE.value:
                    stats['available_tickets'] += 1
                elif ticket.status == TicketStatus.SOLD.value:
                    stats['sold_tickets'] += 1
                    stats['total_sales'] += raffle.ticket_price
                    if ticket.is_revealed:
                        stats['revealed_tickets'] += 1
                elif ticket.status == TicketStatus.VOID.value:
                    stats['void_tickets'] += 1
                elif ticket.status == TicketStatus.CANCELLED.value:
                    stats['cancelled_tickets'] += 1
                
                if ticket.instant_win_eligible:
                    stats['eligible_tickets'] += 1
            
            # Calculate tickets available for sale
            stats['tickets_available_for_sale'] = stats['available_tickets']

            return stats, None

        except SQLAlchemyError as e:
            return None, str(e)
        
    @staticmethod
    def fix_purchase_count_discrepancy(user_id: int, raffle_id: int) -> Tuple[bool, Optional[str]]:
        """Fix discrepancy between actual tickets and purchase count"""
        try:
            with db.session.begin_nested():
                # Get actual ticket count
                actual_count = Ticket.query.filter_by(
                    raffle_id=raffle_id,
                    user_id=user_id,
                    status=TicketStatus.SOLD.value
                ).count()

                # Get or create stats
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

                if stats.tickets_purchased != actual_count:
                    old_count = stats.tickets_purchased
                    stats.tickets_purchased = actual_count
                    logger.info(
                        f"Fixed purchase count for user {user_id} in raffle {raffle_id}. "
                        f"Old: {old_count}, New: {actual_count}"
                    )

            db.session.commit()
            return True, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)