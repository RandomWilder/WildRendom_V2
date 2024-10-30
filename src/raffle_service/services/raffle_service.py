# src/raffle_service/services/raffle_service.py
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_
import logging
from src.shared import db
from src.raffle_service.models import Raffle, RaffleStatus, Ticket, TicketStatus
from src.raffle_service.models.raffle_status_change import RaffleStatusChange
from src.raffle_service.services.ticket_service import TicketService
from src.raffle_service.models import (
    Raffle, RaffleStatus, 
    Ticket, TicketStatus,
    InstantWin, InstantWinStatus
)
from src.raffle_service.services.instant_win_service import InstantWinService

# Status transition definitions
VALID_STATUS_TRANSITIONS = {
    RaffleStatus.DRAFT.value: [
        RaffleStatus.COMING_SOON.value,
        RaffleStatus.ACTIVE.value,
        RaffleStatus.CANCELLED.value
    ],
    RaffleStatus.COMING_SOON.value: [
        RaffleStatus.ACTIVE.value,
        RaffleStatus.INACTIVE.value,
        RaffleStatus.CANCELLED.value
    ],
    RaffleStatus.ACTIVE.value: [
        RaffleStatus.INACTIVE.value,
        RaffleStatus.SOLD_OUT.value,
        RaffleStatus.ENDED.value,
        RaffleStatus.CANCELLED.value
    ],
    RaffleStatus.INACTIVE.value: [
        RaffleStatus.ACTIVE.value,
        RaffleStatus.COMING_SOON.value,
        RaffleStatus.CANCELLED.value
    ],
    RaffleStatus.SOLD_OUT.value: [
        RaffleStatus.ENDED.value
    ],
    RaffleStatus.ENDED.value: [],  # Terminal state
    RaffleStatus.CANCELLED.value: []  # Terminal state
}

class RaffleService:
    @staticmethod
    def _generate_tickets(raffle_id: int, total_tickets: int) -> bool:
        """Generate tickets for a raffle"""
        try:
            tickets = []
            for i in range(total_tickets):
                ticket_number = str(i + 1).zfill(3)
                ticket = Ticket(
                    raffle_id=raffle_id,
                    ticket_number=ticket_number,
                    status=TicketStatus.AVAILABLE.value
                )
                tickets.append(ticket)
            
            db.session.bulk_save_objects(tickets)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

    @staticmethod
    def create_raffle(data: dict, admin_id: int) -> Tuple[Optional[Raffle], Optional[str]]:
        """Create a new raffle"""
        try:
            # Ensure timezone awareness for start and end times
            start_time = data['start_time']
            end_time = data['end_time']
            
            # Handle string inputs
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            elif start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
                
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            elif end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            if start_time >= end_time:
                return None, "End time must be after start time"

            # Validate instant win configuration
            instant_win_count = data.get('instant_win_count', 0)
            total_prize_count = data.get('total_prize_count', 1)
            if instant_win_count > total_prize_count:
                return None, "Instant win count cannot exceed total prize count"

            raffle = Raffle(
                title=data['title'],
                description=data.get('description'),
                total_tickets=data['total_tickets'],
                ticket_price=data['ticket_price'],
                start_time=start_time,
                end_time=end_time,
                status=RaffleStatus.DRAFT.value,
                created_by_id=admin_id,
                instant_win_count=instant_win_count,
                total_prize_count=total_prize_count,
                max_tickets_per_user=data.get('max_tickets_per_user', 10)
            )
            
            db.session.add(raffle)
            db.session.commit()
            
            # Generate tickets
            if not RaffleService._generate_tickets(raffle.id, raffle.total_tickets):
                db.session.delete(raffle)
                db.session.commit()
                return None, "Failed to generate tickets"

            # Handle instant win allocation if configured
            if instant_win_count > 0:
                instant_wins, error = InstantWinService.allocate_instant_wins(
                    raffle_id=raffle.id,
                    count=instant_win_count
                )
                if error:
                    db.session.delete(raffle)
                    db.session.commit()
                    return None, f"Failed to allocate instant wins: {error}"
                
                # Log instant win allocation
                logging.info(f"Created {len(instant_wins)} instant wins for raffle {raffle.id}")
            
            return raffle, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_raffle(raffle_id: int) -> Tuple[Optional[Raffle], Optional[str]]:
        """Get a raffle by ID"""
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
            return raffle, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def get_raffles_by_status(status: RaffleStatus = None) -> Tuple[Optional[List[Raffle]], Optional[str]]:
        """Get all raffles, optionally filtered by status"""
        try:
            query = Raffle.query
            if status:
                query = query.filter_by(status=status.value)
            raffles = query.all()
            return raffles, None
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def update_raffle(raffle_id: int, data: dict, admin_id: int = None) -> Tuple[Optional[Raffle], Optional[str]]:
        """Update raffle details"""
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"

            if raffle.status not in [RaffleStatus.DRAFT.value, RaffleStatus.COMING_SOON.value]:
                return None, "Can only update draft or coming soon raffles"

            # Update allowed fields
            allowed_fields = [
                'title', 'description', 'ticket_price', 
                'start_time', 'end_time', 'prize_pool_id',
                'instant_win_count', 'draw_prize_count'
            ]
            
            for key in allowed_fields:
                if key in data:
                    if key in ['start_time', 'end_time']:
                        try:
                            dt_value = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
                            setattr(raffle, key, dt_value)
                        except ValueError as e:
                            return None, f"Invalid datetime format for {key}: {str(e)}"
                    else:
                        setattr(raffle, key, data[key])

            raffle.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return raffle, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_raffle_status(raffle_id: int, new_status: RaffleStatus, admin_id: int) -> Tuple[Optional[Raffle], Optional[str]]:
        """Update raffle status"""
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"

            # Ensure we're working with the value, not enum
            new_status_value = new_status.value if isinstance(new_status, RaffleStatus) else new_status
            
            # Validate status transition
            if not RaffleService._is_valid_status_transition(raffle.status, new_status_value):
                return None, (
                    f"Invalid status transition from {raffle.status} to {new_status_value}. "
                    f"Valid transitions are: {VALID_STATUS_TRANSITIONS.get(raffle.status, [])}"
                )

            # Validate time-based conditions using the model's method
            is_valid, error_message = raffle.validate_status_change(new_status_value)
            if not is_valid:
                return None, error_message

            # Update the status
            raffle.status = new_status_value
            raffle.updated_at = datetime.now(timezone.utc)
            
            # Record the change
            status_change = RaffleStatusChange(
                raffle_id=raffle.id,
                previous_status=raffle.status,
                new_status=new_status_value,
                changed_by_id=admin_id,
                reason="Admin status update"
            )
            
            db.session.add(status_change)
            db.session.commit()
            
            return raffle, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def _is_valid_status_transition(current_status: str, new_status: str) -> bool:
        """Check if status transition is valid"""
        return new_status in VALID_STATUS_TRANSITIONS.get(current_status, [])

    @staticmethod
    def purchase_tickets(raffle_id: int, user_id: int, quantity: int, transaction_id: int) -> Tuple[Optional[List[Ticket]], Optional[str]]:
        """Purchase tickets for a raffle"""
        try:
            raffle, error = RaffleService.get_raffle(raffle_id)
            if error:
                return None, error

            if not raffle.can_purchase_tickets():
                return None, f"Cannot purchase tickets for raffle in {raffle.status} status"

            return TicketService.purchase_tickets(
                user_id=user_id,
                raffle_id=raffle_id,
                quantity=quantity,
                transaction_id=transaction_id
            )
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_raffle_status_changes(raffle_id: int) -> Tuple[Optional[List[RaffleStatusChange]], Optional[str]]:
        """Get status change history for a raffle"""
        try:
            changes = RaffleStatusChange.query.filter_by(raffle_id=raffle_id)\
                .order_by(RaffleStatusChange.created_at.desc()).all()
            return changes, None
        except SQLAlchemyError as e:
            return None, str(e)