from typing import Optional, Tuple, Dict
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from src.shared import db
from decimal import Decimal
from src.raffle_service.models.ticket_reservation import TicketReservation, ReservationStatus, ReservedTicket
from src.raffle_service.models.ticket import Ticket, TicketStatus
from src.user_service.models import User, CreditTransaction
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    def create_payment_intent(
        reservation_id: str,
        user_id: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Create a payment intent for a reservation"""
        try:
            # Get reservation with locking
            reservation = db.session.query(TicketReservation).with_for_update().get(reservation_id)
            if not reservation:
                return None, "Reservation not found"

            # Accept either PENDING or ACTIVE status
            if reservation.status not in [ReservationStatus.PENDING.value, ReservationStatus.ACTIVE.value]:
                return None, f"Cannot process payment for reservation in {reservation.status} status"

            if reservation.user_id != user_id:
                return None, "Not authorized to pay for this reservation"

            # Check if reservation is expired
            expires_at = reservation.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) > expires_at:
                return None, "Reservation has expired"

            # Get user's available credits
            user = db.session.query(User).with_for_update().get(user_id)
            if not user:
                return None, "User not found"

            # Convert all monetary values to Decimal
            available_credits = Decimal(str(user.site_credits))
            total_amount = reservation.total_amount

            # Process the credit payment
            if available_credits >= total_amount:
                # Create credit transaction
                transaction = CreditTransaction(
                    user_id=user_id,
                    amount=-total_amount,  # Negative for deduction
                    transaction_type='subtract',
                    balance_after=float(available_credits - total_amount),
                    reference_type='ticket_purchase',
                    reference_id=reservation_id,
                    created_by_id=user_id
                )

                # Update user's balance
                user.site_credits = float(available_credits - total_amount)

                # Update reservation status
                reservation.status = ReservationStatus.CONFIRMED.value

                db.session.add(transaction)
                db.session.commit()

                return {
                    "status": "succeeded",
                    "payment_intent": {
                        "id": f"pi_{reservation_id}",
                        "amount": float(total_amount),
                        "currency": "USD",
                        "status": "succeeded"
                    },
                    "payment_breakdown": {
                        "site_credit": {
                            "amount": float(total_amount),
                            "status": "applied"
                        }
                    }
                }, None

            else:
                # User needs to pay with real money for remaining amount
                remaining_amount = total_amount - available_credits
                return {
                    "status": "requires_payment_method",
                    "payment_intent": {
                        "id": f"pi_{reservation_id}",
                        "amount": float(total_amount),
                        "currency": "USD",
                        "status": "requires_payment_method"
                    },
                    "payment_breakdown": {
                        "site_credit": {
                            "amount": float(available_credits),
                            "status": "ready"
                        },
                        "real_money": {
                            "amount": float(remaining_amount),
                            "status": "requires_payment_method"
                        }
                    }
                }, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in create_payment_intent: {str(e)}")
            return None, str(e)

    @staticmethod
    def confirm_payment(
        payment_intent_id: str,
        user_id: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Confirm payment and finalize ticket purchase"""
        try:
            # Extract reservation_id from payment_intent_id
            reservation_id = payment_intent_id.replace('pi_', '')
            
            reservation = db.session.query(TicketReservation).with_for_update().get(reservation_id)
            if not reservation:
                return None, "Reservation not found"

            if reservation.status == ReservationStatus.COMPLETED.value:
                return {
                    "status": "already_completed",
                    "reservation_id": reservation_id
                }, None

            if reservation.user_id != user_id:
                return None, "Not authorized to confirm this payment"

            # Get reserved tickets
            reserved_tickets = db.session.query(Ticket).join(
                ReservedTicket,
                ReservedTicket.ticket_id == Ticket.id
            ).filter(
                ReservedTicket.reservation_id == reservation_id
            ).with_for_update().all()

            # Update tickets status
            for ticket in reserved_tickets:
                ticket.status = TicketStatus.SOLD.value
                ticket.user_id = user_id
                ticket.purchase_time = datetime.now(timezone.utc)

            # Update reservation status
            reservation.status = ReservationStatus.COMPLETED.value
            reservation.completed_at = datetime.now(timezone.utc)

            db.session.commit()

            return {
                "status": "succeeded",
                "reservation_id": reservation_id,
                "completed_at": reservation.completed_at.isoformat(),
                "tickets": [{
                    "ticket_id": ticket.ticket_id,
                    "ticket_number": ticket.ticket_number
                } for ticket in reserved_tickets]
            }, None

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in confirm_payment: {str(e)}")
            return None, str(e)