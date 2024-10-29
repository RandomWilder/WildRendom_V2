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
    def get_raffle_statistics(raffle_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Get ticket statistics for a raffle"""
        try:
            stats = {
                'total_tickets': 0,
                'available_tickets': 0,
                'sold_tickets': 0,
                'void_tickets': 0,
                'cancelled_tickets': 0,
                'total_sales': 0.0,
                'total_instant_wins': 0,
                'available_instant_wins': 0,
                'claimed_instant_wins': 0,
                'unique_participants': 0,  # New field
                'tickets_available_for_sale': 0  # New field
            }
            
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"

            # Get counts for each status
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
                    if ticket.instant_win:
                        stats['available_instant_wins'] += 1
                elif ticket.status == TicketStatus.SOLD.value:
                    stats['sold_tickets'] += 1
                    stats['total_sales'] += raffle.ticket_price
                    if ticket.instant_win:
                        stats['claimed_instant_wins'] += 1
                elif ticket.status == TicketStatus.VOID.value:
                    stats['void_tickets'] += 1
                elif ticket.status == TicketStatus.CANCELLED.value:
                    stats['cancelled_tickets'] += 1
                
                if ticket.instant_win:
                    stats['total_instant_wins'] += 1
            
            # Calculate tickets available for sale
            stats['tickets_available_for_sale'] = stats['available_tickets']

            return stats, None
        except SQLAlchemyError as e:
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
        """Purchase tickets for a raffle"""
        try:
            # Existing validation code...
            
            # Get available tickets randomly
            available_tickets = Ticket.query.filter_by(
                raffle_id=raffle_id,
                status=TicketStatus.AVAILABLE.value
            ).order_by(func.random()).limit(quantity).all()

            if len(available_tickets) < quantity:
                return None, "Not enough tickets available"

            # Update tickets
            purchase_time = datetime.now(timezone.utc)
            purchased_tickets = []
            instant_wins_found = []

            for ticket in available_tickets:
                ticket.user_id = user_id
                ticket.status = TicketStatus.SOLD.value
                ticket.purchase_time = purchase_time
                ticket.transaction_id = transaction_id
                purchased_tickets.append(ticket)
                
                # Check for instant win
                if ticket.instant_win:
                    instant_win, error = InstantWinService.check_instant_win(ticket.id)
                    if instant_win and not error:
                        instant_wins_found.append(instant_win)

            # Update purchase count
            success, error = PurchaseLimitService.update_purchase_count(
                user_id=user_id,
                raffle_id=raffle_id,
                quantity=quantity
            )
            
            if not success:
                db.session.rollback()
                return None, error

            db.session.commit()
            
            # If instant wins were found, we should trigger notifications
            # This will be handled by the Prize Service in the future
            if instant_wins_found:
                for win in instant_wins_found:
                    # TODO: Trigger notification to Prize Service
                    pass
            
            return purchased_tickets, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Database error: {str(e)}"