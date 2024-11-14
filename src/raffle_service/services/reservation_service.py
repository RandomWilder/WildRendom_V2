from typing import Optional, Tuple, Dict
from datetime import datetime, timezone, timedelta
from src.shared import db
from src.user_service.models import User
from src.raffle_service.models import Raffle, Ticket
from src.raffle_service.models.ticket_reservation import TicketReservation, ReservedTicket
import logging
import uuid

logger = logging.getLogger(__name__)

class ReservationService:
    @staticmethod
    def create_reservation(user_id: int, raffle_id: int, quantity: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Create a ticket reservation"""
        try:
            # 1. Verify raffle exists and is active
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
            
            if not raffle.can_purchase_tickets():
                return None, f"Cannot purchase tickets for raffle in {raffle.status} status"

            current_time = datetime.now(timezone.utc)
            expiry_time = current_time + timedelta(minutes=5)
            
            # Ensure raffle end_time is timezone-aware
            raffle_end_time = raffle.end_time if raffle.end_time.tzinfo else raffle.end_time.replace(tzinfo=timezone.utc)
            
            # Adjust expiry time if close to raffle end
            time_to_end = raffle_end_time - current_time
            if time_to_end < timedelta(minutes=5):
                if time_to_end <= timedelta(minutes=2):
                    return None, "Too close to raffle end time"
                expiry_time = raffle_end_time - timedelta(minutes=1)

            # Generate unique reservation ID
            reservation_id = f"res_{uuid.uuid4().hex[:16]}"

            # 2. Get random available tickets
            available_tickets = Ticket.query.filter_by(
                raffle_id=raffle_id,
                status='available'
            ).order_by(db.func.random()).limit(quantity).all()

            if len(available_tickets) < quantity:
                return None, "Not enough tickets available"

            # Create reservation object
            reservation = TicketReservation(
                id=reservation_id,
                user_id=user_id,
                raffle_id=raffle_id,
                quantity=quantity,
                total_amount=quantity * raffle.ticket_price,
                status='active',
                expires_at=expiry_time
            )

            # Get user's available credits
            user = User.query.get(user_id)
            site_credit_available = min(user.site_credits, reservation.total_amount)
            remaining_amount = max(0, reservation.total_amount - site_credit_available)

            # Save everything to database
            db.session.add(reservation)
            
            # Create reserved tickets
            for ticket in available_tickets:
                reserved_ticket = ReservedTicket(
                    reservation_id=reservation.id,
                    ticket_id=ticket.id,
                    status='reserved'
                )
                db.session.add(reserved_ticket)

            db.session.commit()

            return {
                "reservation": {
                    "id": reservation.id,
                    "status": "active",
                    "expiry_time": expiry_time.isoformat()
                },
                "tickets": {
                    "raffle_id": raffle_id,
                    "quantity": quantity,
                    "total_amount": float(reservation.total_amount),
                    "payment_options": {
                        "site_credit_available": float(site_credit_available),
                        "remaining_amount": float(remaining_amount)
                    }
                }
            }, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error in create_reservation: {str(e)}")
            return None, str(e)