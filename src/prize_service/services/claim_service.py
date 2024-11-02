# src/prize_service/services/claim_service.py

from typing import Optional, Tuple, Dict
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from src.shared import db
from src.raffle_service.models import InstantWin, InstantWinStatus
from src.prize_service.models import Prize
from src.user_service.services.user_service import UserService

class ClaimService:
    @staticmethod
    def process_instant_win_claim(
        instant_win_id: int,
        user_id: int,
        claim_method: str
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Process an instant win claim"""
        try:
            # Get instant win record
            instant_win = InstantWin.query.get(instant_win_id)
            if not instant_win:
                return None, "Instant win not found"

            # Verify ownership
            if instant_win.ticket.user_id != user_id:
                return None, "Not authorized to claim this prize"

            # Verify status
            if instant_win.status != InstantWinStatus.PENDING.value:
                return None, f"Invalid instant win status: {instant_win.status} (must be pending)"

            # Only handle credit claims for now
            if claim_method != 'credit':
                return None, "Only credit claims are supported at this time"

            # Get the prize details
            try:
                prize_id = int(instant_win.prize_reference)  # Convert prize reference to ID
                prize = Prize.query.get(prize_id)
                if not prize:
                    return None, "Prize configuration not found"
                
                prize_value = float(prize.credit_value)  # Convert Decimal to float
            except (ValueError, AttributeError):
                return None, "Invalid prize configuration"

            # Use the existing credit system to award the prize
            _, error = UserService.update_credits(
                user_id=user_id,
                amount=prize_value,
                transaction_type='add',
                reference_type='prize_claim',
                reference_id=str(instant_win_id),
                notes=f'Prize claim for {prize.name} (ID:{prize.id}) worth {prize_value} credits'
            )

            if error:
                return None, f"Failed to process credit claim: {error}"

            # Update instant win status
            instant_win.status = InstantWinStatus.CLAIMED.value
            prize.total_claimed += 1  # Update prize claim counter
            db.session.commit()

            return {
                'instant_win_id': instant_win_id,
                'prize_id': prize.id,
                'prize_name': prize.name,
                'claim_method': claim_method,
                'claimed_at': datetime.now(timezone.utc).isoformat(),
                'status': InstantWinStatus.CLAIMED.value,
                'prize_value': prize_value
            }, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)