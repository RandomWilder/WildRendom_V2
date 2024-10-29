# scripts/test_instant_win.py

from pathlib import Path
import sys
from datetime import datetime, timezone

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db
from src.shared.config import config
from src.raffle_service.models.raffle import Raffle, RaffleStatus
from src.raffle_service.models.ticket import Ticket, TicketStatus
from src.raffle_service.models.instant_win import InstantWin, InstantWinStatus
from src.raffle_service.services.instant_win_service import InstantWinService

def test_instant_win_setup():
    """Test InstantWin functionality setup"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    
    with app.app_context():
        try:
            # Create a test raffle
            raffle = Raffle(
                title="Test Raffle",
                description="Testing InstantWin",
                total_tickets=100,
                ticket_price=10.0,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                status=RaffleStatus.DRAFT.value,
                created_by_id=1,  # Admin user
                instant_win_count=5,
                total_prize_count=5,
                max_tickets_per_user=10
            )
            db.session.add(raffle)
            db.session.commit()
            
            print(f"Created test raffle with ID: {raffle.id}")
            
            # Create 100 tickets for the raffle
            print("Creating tickets...")
            tickets = []
            for i in range(100):
                ticket = Ticket(
                    raffle_id=raffle.id,
                    ticket_number=str(i+1).zfill(3),
                    status=TicketStatus.AVAILABLE.value,
                    instant_win=False
                )
                tickets.append(ticket)
            
            db.session.bulk_save_objects(tickets)
            db.session.commit()
            print(f"Created {len(tickets)} tickets")
            
            # Try to allocate instant wins
            instant_wins, error = InstantWinService.allocate_instant_wins(raffle.id, 5)
            
            if error:
                print(f"Error allocating instant wins: {error}")
            else:
                print(f"Successfully allocated {len(instant_wins)} instant wins")
                
                # Verify the allocations
                tickets_with_wins = Ticket.query.filter_by(
                    raffle_id=raffle.id,
                    instant_win=True
                ).count()
                
                print(f"Tickets marked as instant wins: {tickets_with_wins}")
                print(f"InstantWin records created: {len(instant_wins)}")
                
        except Exception as e:
            print(f"Test failed: {str(e)}")
            db.session.rollback()
            raise  # Add this to see full traceback if needed

if __name__ == "__main__":
    test_instant_win_setup()