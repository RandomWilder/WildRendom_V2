# src/raffle_service/services/instant_win_service.py

from typing import Optional, Tuple, List, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload
from src.shared import db
from src.raffle_service.models import InstantWin, InstantWinStatus
from src.raffle_service.models.ticket import Ticket, TicketStatus
from src.raffle_service.models.raffle import Raffle, RaffleStatus
from src.prize_service.models import PrizeAllocation, AllocationType, ClaimStatus, PrizePool
from src.prize_service.services.prize_service import PrizeService
import logging

logger = logging.getLogger(__name__)

class InstantWinService:
    @staticmethod
    def check_instant_win(ticket_id: int) -> Tuple[Optional[InstantWin], Optional[str]]:
        """Check if a ticket is an instant winner when revealed"""
        try:
            # Get instant win with transaction safety
            instant_win = db.session.query(InstantWin)\
                .filter_by(
                    ticket_id=ticket_id,
                    status=InstantWinStatus.ALLOCATED.value
                )\
                .first()
            
            if not instant_win:
                return None, None

            # Get the ticket and raffle info with efficient loading
            ticket = db.session.query(Ticket)\
                .options(joinedload('raffle'))\
                .filter_by(id=ticket_id)\
                .first()

            if not ticket or not ticket.raffle:
                return None, "Invalid ticket configuration"

            if not ticket.raffle.prize_pool_id:
                logger.error(f"No prize pool configured for raffle {ticket.raffle_id}")
                return None, "Raffle has no prize pool configured"

            # Use PrizeService to allocate prize with instance selection
            allocation, error = PrizeService.allocate_instant_win(
                pool_id=ticket.raffle.prize_pool_id,
                ticket_id=str(ticket_id),
                user_id=ticket.user_id
            )
            
            if error:
                logger.error(f"Error allocating prize: {error}")
                return None, error

            # Update instant win record with enhanced tracking
            instant_win.prize_reference = str(allocation.id)
            instant_win.discover()
            instant_win.claim_deadline = allocation.claim_deadline

            # Track the specific instance ID for better monitoring
            if allocation.instance_identifier:
                instant_win.instance_reference = allocation.instance_identifier
            
            # Update ticket status
            ticket.status = TicketStatus.REVEALED.value
            ticket.reveal_time = datetime.now(timezone.utc)
            ticket.instant_win = True

            db.session.commit()
            logger.info(
                f"Instant win discovered for ticket {ticket_id}, "
                f"prize allocation {allocation.id}, "
                f"instance {allocation.instance_identifier}"
            )
            return instant_win, None
                
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in check_instant_win: {str(e)}")
            return None, str(e)

    @staticmethod
    def allocate_instant_wins(raffle_id: int, count: int) -> Tuple[Optional[List[InstantWin]], Optional[str]]:
        """Enhanced instant win allocation with instance tracking"""
        try:
            # Get raffle with locking
            raffle = db.session.query(Raffle).get(raffle_id)
            if not raffle:
                return None, "Raffle not found"
            
            # Prevent allocation after raffle starts
            if raffle.status != RaffleStatus.DRAFT.value:
                return None, "Instant wins can only be allocated in draft status"
            
            # Check if instant wins already allocated
            existing_count = InstantWin.query.filter_by(raffle_id=raffle_id).count()
            if existing_count > 0:
                return None, "Instant wins already allocated for this raffle"

            # Verify prize pool configuration
            if not raffle.prize_pool_id:
                return None, "Raffle has no prize pool configured"

            pool = db.session.query(PrizePool).get(raffle.prize_pool_id)
            if not pool:
                return None, "Prize pool not found"

            # Verify pool has enough available instances
            if pool.available_prizes < count:
                return None, f"Not enough available prizes in pool. Needed: {count}, Available: {pool.available_prizes}"
            
            # Get random available tickets that are marked as eligible
            available_tickets = db.session.query(Ticket)\
                .filter_by(
                    raffle_id=raffle_id,
                    status=TicketStatus.AVAILABLE.value,
                    instant_win_eligible=True
                )\
                .order_by(func.random())\
                .limit(count)\
                .all()
            
            if len(available_tickets) < count:
                return None, f"Not enough eligible tickets. Requested {count}, found {len(available_tickets)}"
            
            instant_wins = []
            for ticket in available_tickets:
                instant_win = InstantWin(
                    raffle_id=raffle_id,
                    ticket_id=ticket.id,
                    prize_reference=f"pending_win_{raffle_id}_{ticket.id}",
                    status=InstantWinStatus.ALLOCATED.value,
                    created_at=datetime.now(timezone.utc)
                )
                instant_wins.append(instant_win)
                ticket.instant_win = True
            
            db.session.bulk_save_objects(instant_wins)
            db.session.commit()
            
            logger.info(
                f"Successfully allocated {len(instant_wins)} instant wins "
                f"for raffle {raffle_id} using prize pool {pool.id}"
            )
            return instant_wins, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in allocate_instant_wins: {str(e)}")
            return None, str(e)

    @staticmethod
    def initiate_claim(instant_win_id: int, user_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Initiate claim process with enhanced value options"""
        try:
            instant_win = db.session.query(InstantWin).get(instant_win_id)
            if not instant_win:
                return None, "Instant win not found"
            
            if instant_win.status != InstantWinStatus.DISCOVERED.value:
                return None, f"Invalid instant win status: {instant_win.status}"
            
            if not instant_win.prize_reference:
                return None, "No prize allocation found"

            # Get the prize allocation
            allocation = db.session.query(PrizeAllocation).get(instant_win.prize_reference)
            if not allocation:
                return None, "Prize allocation not found"

            # Verify ownership
            if allocation.winner_user_id != user_id:
                return None, "Not authorized to claim this prize"

            # Mark instant win as pending claim
            instant_win.status = InstantWinStatus.PENDING.value
            db.session.commit()

            # Get prize instance details for UI
            prize = allocation.prize
            if not prize:
                return None, "Prize details not found"

            # Return enhanced claim information
            return {
                'instant_win_id': instant_win.id,
                'allocation_id': allocation.id,
                'instance_id': allocation.instance_identifier,
                'prize_name': prize.name,
                'prize_type': prize.type,
                'prize_tier': prize.tier,
                'claim_deadline': allocation.claim_deadline.isoformat(),
                'claim_method': prize.claim_processor_type,
                'value_options': {
                    'retail': float(prize.retail_value),
                    'cash': float(prize.cash_value),
                    'credit': float(prize.credit_value)
                },
                'claim_rules': {
                    'expiry_days': prize.expiry_days,
                    'auto_claim_enabled': prize.auto_claim_credit,
                    'claim_methods_available': [prize.claim_processor_type]
                }
            }, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in initiate_claim: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_instant_win_stats(raffle_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Enhanced statistics with instance tracking"""
        try:
            stats = {
                'total_allocated': 0,
                'discovered': 0,
                'pending_claims': 0,
                'claimed': 0,
                'expired': 0,
                'prize_distribution': {},
                'instance_tracking': {
                    'total_instances': 0,
                    'instances_by_status': {}
                }
            }
            
            instant_wins = db.session.query(InstantWin)\
                .filter_by(raffle_id=raffle_id)\
                .all()
            
            for win in instant_wins:
                stats['total_allocated'] += 1
                if win.status == InstantWinStatus.DISCOVERED.value:
                    stats['discovered'] += 1
                elif win.status == InstantWinStatus.PENDING.value:
                    stats['pending_claims'] += 1
                elif win.status == InstantWinStatus.CLAIMED.value:
                    stats['claimed'] += 1
                elif win.status == InstantWinStatus.EXPIRED.value:
                    stats['expired'] += 1

                # Track prize and instance distribution
                if win.prize_reference and win.prize_reference.isdigit():
                    allocation = PrizeAllocation.query.get(int(win.prize_reference))
                    if allocation and allocation.prize:
                        prize_name = allocation.prize.name
                        if prize_name not in stats['prize_distribution']:
                            stats['prize_distribution'][prize_name] = {
                                'count': 0,
                                'instances': {}
                            }
                        stats['prize_distribution'][prize_name]['count'] += 1
                        
                        # Track instance information
                        if allocation.instance_identifier:
                            instance_status = allocation.status
                            stats['instance_tracking']['total_instances'] += 1
                            if instance_status not in stats['instance_tracking']['instances_by_status']:
                                stats['instance_tracking']['instances_by_status'][instance_status] = 0
                            stats['instance_tracking']['instances_by_status'][instance_status] += 1
            
            return stats, None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_instant_win_stats: {str(e)}")
            return None, str(e)