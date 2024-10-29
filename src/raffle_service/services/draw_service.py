# src/raffle_service/services/draw_service.py
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import func
from src.shared import db
from src.raffle_service.models import Ticket, TicketStatus, Raffle, RaffleStatus

class DrawService:
    @staticmethod
    def execute_draw(raffle_id: int, admin_id: int) -> Tuple[Optional[Ticket], Optional[str]]:
        """Execute a prize draw for a raffle"""
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
                
            if raffle.status not in [RaffleStatus.ENDED.value, RaffleStatus.SOLD_OUT.value]:
                return None, "Raffle must be ended or sold out to execute draw"

            # Get all sold tickets for the raffle
            eligible_tickets = Ticket.query.filter(
                Ticket.raffle_id == raffle_id,
                Ticket.status == TicketStatus.SOLD.value
            ).all()
            
            if not eligible_tickets:
                return None, "No eligible tickets for draw"

            # Randomly select a winner
            winning_ticket = DrawService._select_random_winner(eligible_tickets)
            
            if not winning_ticket:
                return None, "Failed to select winner"

            return winning_ticket, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def _select_random_winner(tickets: List[Ticket]) -> Optional[Ticket]:
        """Randomly select a winning ticket"""
        if not tickets:
            return None
        return tickets[int(func.random() * len(tickets))]

    @staticmethod
    def verify_instant_win(ticket_id: int) -> Tuple[Optional[bool], Optional[str]]:
        """Verify if a ticket is an instant winner"""
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                return None, "Ticket not found"
                
            if ticket.status != TicketStatus.SOLD.value:
                return None, "Ticket is not eligible for instant win verification"

            return ticket.instant_win, None
            
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def execute_multiple_draws(raffle_id: int, admin_id: int, number_of_draws: int) -> Tuple[Optional[List[Ticket]], Optional[str]]:
        """Execute multiple prize draws for a raffle"""
        try:
            winners = []
            used_ticket_ids = set()
            
            for _ in range(number_of_draws):
                winning_ticket, error = DrawService.execute_draw(raffle_id, admin_id)
                if error:
                    return None, error
                    
                if winning_ticket.id in used_ticket_ids:
                    continue  # Skip duplicate winners
                    
                winners.append(winning_ticket)
                used_ticket_ids.add(winning_ticket.id)
                
            return winners, None
            
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def assign_instant_wins(raffle_id: int, count: int) -> Tuple[Optional[List[Ticket]], Optional[str]]:
        """Pre-assign instant win tickets randomly"""
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
                
            if raffle.status != RaffleStatus.DRAFT.value:
                return None, "Instant wins can only be assigned in draft status"

            # Get all available tickets
            available_tickets = Ticket.query.filter(
                Ticket.raffle_id == raffle_id,
                Ticket.status == TicketStatus.AVAILABLE.value
            ).all()
            
            if len(available_tickets) < count:
                return None, "Not enough available tickets"

            # Randomly select tickets for instant wins
            instant_win_tickets = DrawService._select_random_winners(available_tickets, count)
            
            # Mark selected tickets as instant winners
            for ticket in instant_win_tickets:
                ticket.instant_win = True
                
            db.session.commit()
            return instant_win_tickets, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def _select_random_winners(tickets: List[Ticket], count: int) -> List[Ticket]:
        """Randomly select multiple winning tickets"""
        import random
        if count > len(tickets):
            return tickets
        return random.sample(tickets, count)