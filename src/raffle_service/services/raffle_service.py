# src/raffle_service/services/raffle_service.py
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
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
from src.prize_service.models import PrizePool, PoolStatus

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
    def _generate_tickets(raffle_id: int, total_tickets: int, instant_win_count: int = 0, prize_pool_id: Optional[int] = None) -> bool:
        """Generate tickets for a raffle with instant win configuration"""
        try:
            tickets = []
            for i in range(total_tickets):
                ticket_number = str(i + 1).zfill(3)
                ticket = Ticket(
                    raffle_id=raffle_id,
                    ticket_id=f"{raffle_id}-{ticket_number}",
                    ticket_number=ticket_number,
                    status=TicketStatus.AVAILABLE.value,
                    instant_win=False,
                    instant_win_eligible=False
                )
                tickets.append(ticket)
            
            db.session.bulk_save_objects(tickets)
            db.session.flush()

            if instant_win_count > 0 and prize_pool_id:
                # Verify prize pool
                pool = PrizePool.query.get(prize_pool_id)
                if not pool or pool.status != PoolStatus.LOCKED.value:
                    return False
                
                # Select random tickets for instant win eligibility
                eligible_tickets = Ticket.query.filter_by(
                    raffle_id=raffle_id,
                    status=TicketStatus.AVAILABLE.value
                ).order_by(func.random()).limit(instant_win_count).all()

                for ticket in eligible_tickets:
                    ticket.instant_win_eligible = True
                    ticket.instant_win = True

            db.session.commit()
            return True

        except SQLAlchemyError:
            db.session.rollback()
            return False

    @staticmethod
    def create_raffle(data: dict, admin_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Create a new raffle with prize pool integration"""
        try:
            # Validate prize pool
            prize_pool = PrizePool.query.get(data['prize_pool_id'])
            if not prize_pool:
                return None, "Prize pool not found"
            if prize_pool.status != PoolStatus.LOCKED.value:
                return None, "Prize pool must be locked"

            # Validate draw configuration
            draw_config = data['draw_configuration']
            if draw_config['number_of_draws'] < 1:
                return None, "Number of draws must be at least 1"
            if draw_config['distribution_type'] not in ['single', 'split']:
                return None, "Invalid distribution type"

            # Create raffle
            raffle = Raffle(
                title=data['title'],
                description=data.get('description'),
                total_tickets=data['total_tickets'],
                ticket_price=data['ticket_price'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                status=RaffleStatus.DRAFT.value,
                max_tickets_per_user=data['max_tickets_per_user'],
                prize_pool_id=prize_pool.id,
                draw_count=draw_config['number_of_draws'],
                draw_distribution_type=draw_config['distribution_type'],
                created_by_id=admin_id
            )
            
            db.session.add(raffle)
            db.session.flush()  # Get raffle ID

            # Generate tickets
            tickets_created = RaffleService._generate_tickets(
                raffle_id=raffle.id,
                total_tickets=raffle.total_tickets,
                instant_win_count=prize_pool.instant_win_count,
                prize_pool_id=prize_pool.id
            )
            
            if not tickets_created:
                db.session.rollback()
                return None, "Failed to generate tickets"

            db.session.commit()

            # Prepare response according to API spec
            response = raffle.to_dict()
            response.update({
                'tickets': {
                    'total_generated': raffle.total_tickets,
                    'instant_win_eligible': prize_pool.instant_win_count
                },
                'draw_configuration': {
                    'number_of_draws': raffle.draw_count,
                    'distribution_type': raffle.draw_distribution_type,
                    'prize_value_per_draw': float(prize_pool.credit_total / raffle.draw_count) if raffle.draw_distribution_type == 'split' else float(prize_pool.credit_total),
                    'draw_time': raffle.end_time.isoformat()
                },
                'claim_deadlines': {
                    'instant_win': (raffle.end_time + timedelta(hours=2)).isoformat(),
                    'draw_win': (raffle.end_time + timedelta(days=14)).isoformat()
                }
            })

            return response, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in create_raffle: {str(e)}")
            return None, str(e)
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in create_raffle: {str(e)}")
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
    def purchase_tickets(raffle_id: int, user_id: int, quantity: int, transaction_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Purchase tickets with instant win integration"""
        try:
            raffle, error = RaffleService.get_raffle(raffle_id)
            if error:
                return None, error

            if not raffle.can_purchase_tickets():
                return None, f"Cannot purchase tickets for raffle in {raffle.status} status"

            # Purchase tickets through ticket service
            tickets, error = TicketService.purchase_tickets(
                user_id=user_id,
                raffle_id=raffle_id,
                quantity=quantity,
                transaction_id=transaction_id
            )
            
            if error:
                return None, error

            # Format response according to API spec
            response = {
                'tickets': [
                    {
                        'ticket_id': ticket.ticket_id,
                        'ticket_number': ticket.ticket_number,
                        'purchase_time': ticket.purchase_time.isoformat(),
                        'status': ticket.status,
                        'transaction_id': str(transaction_id)
                    } for ticket in tickets
                ],
                'transaction': {
                    'amount': raffle.ticket_price * quantity,
                    'transaction_id': str(transaction_id)
                }
            }

            return response, None

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