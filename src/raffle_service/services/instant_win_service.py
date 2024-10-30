# src/raffle_service/services/instant_win_service.py

from typing import Optional, Tuple, List, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from src.shared import db
from src.raffle_service.models import Raffle, Ticket, InstantWin, InstantWinStatus
from src.raffle_service.models.ticket import TicketStatus
from src.raffle_service.models.raffle import RaffleStatus
from src.prize_service.models import PrizeAllocation, AllocationType, ClaimStatus

class InstantWinService:
    @staticmethod
    def allocate_instant_wins(raffle_id: int, count: int) -> Tuple[Optional[List[InstantWin]], Optional[str]]:
        """
        Allocate instant wins to random tickets during raffle creation
        """
        try:
            raffle = Raffle.query.get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
            
            # Prevent allocation after raffle starts
            if raffle.status != RaffleStatus.DRAFT.value:
                return None, "Instant wins can only be allocated in draft status"
            
            # Check if instant wins already allocated
            existing_count = InstantWin.query.filter_by(raffle_id=raffle_id).count()
            if existing_count > 0:
                return None, "Instant wins already allocated for this raffle"
            
            # Get random available tickets
            available_tickets = Ticket.query.filter_by(
                raffle_id=raffle_id,
                status=TicketStatus.AVAILABLE.value
            ).order_by(func.random()).limit(count).all()
            
            if len(available_tickets) < count:
                return None, f"Not enough available tickets. Requested {count}, found {len(available_tickets)}"
            
            instant_wins = []
            for ticket in available_tickets:
                instant_win = InstantWin(
                    raffle_id=raffle_id,
                    ticket_id=ticket.id,
                    prize_reference=f"instant_win_{raffle_id}_{ticket.id}"  # Placeholder for Prize Service
                )
                instant_wins.append(instant_win)
                # Mark ticket as instant win
                ticket.instant_win = True
            
            db.session.bulk_save_objects(instant_wins)
            db.session.commit()
            
            return instant_wins, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def check_instant_win(ticket_id: int) -> Tuple[Optional[InstantWin], Optional[str]]:
        """Check if a ticket is an instant winner when purchased"""
        try:
            instant_win = InstantWin.query.filter_by(
                ticket_id=ticket_id,
                status=InstantWinStatus.ALLOCATED.value
            ).first()
            
            if instant_win:
                instant_win.discover()
                
                # Create prize allocation
                allocation = PrizeAllocation(
                    prize_id=1,  # We'll need to get this from prize pool
                    pool_id=2,   # We'll need to get this from instant win configuration
                    allocation_type=AllocationType.INSTANT_WIN.value,
                    reference_type='ticket',
                    reference_id=str(ticket_id),
                    winner_user_id=instant_win.ticket.user_id,
                    won_at=datetime.now(timezone.utc),
                    claim_status=ClaimStatus.PENDING.value,
                    claim_deadline=datetime.now(timezone.utc) + timedelta(days=1),
                    created_by_id=instant_win.ticket.user_id
                )
                
                db.session.add(allocation)
                db.session.commit()
                
                return instant_win, None
                
            return None, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def initiate_claim(instant_win_id: int, user_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Initiate claim process (will be handled by Prize Service)
        """
        try:
            instant_win = InstantWin.query.get(instant_win_id)
            if not instant_win:
                return None, "Instant win not found"
            
            if instant_win.status != InstantWinStatus.DISCOVERED.value:
                return None, f"Invalid instant win status: {instant_win.status}"
            
            # Mark as pending claim
            instant_win.mark_pending_claim()
            db.session.commit()
            
            # Return claim information (to be used by Prize Service)
            return {
                'instant_win_id': instant_win.id,
                'prize_reference': instant_win.prize_reference,
                'user_id': user_id,
                'claim_deadline': instant_win.claim_deadline.isoformat()
            }, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def get_instant_win_stats(raffle_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get statistics about instant wins for a raffle
        """
        try:
            stats = {
                'total_allocated': 0,
                'discovered': 0,
                'pending_claims': 0,
                'claimed': 0,
                'expired': 0
            }
            
            instant_wins = InstantWin.query.filter_by(raffle_id=raffle_id).all()
            
            for win in instant_wins:
                stats['total_allocated'] += 1
                if win.status == InstantWinStatus.DISCOVERED.value:
                    stats['discovered'] += 1
                elif win.status == InstantWinStatus.PENDING_CLAIM.value:
                    stats['pending_claims'] += 1
                elif win.status == InstantWinStatus.CLAIMED.value:
                    stats['claimed'] += 1
                elif win.status == InstantWinStatus.EXPIRED.value:
                    stats['expired'] += 1
            
            return stats, None
            
        except SQLAlchemyError as e:
            return None, str(e)