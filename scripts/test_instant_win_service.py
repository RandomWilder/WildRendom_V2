# scripts/test_instant_win_service.py

from pathlib import Path
import sys
from datetime import datetime, timezone
import sqlite3

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

def reset_instant_wins():
    """Reset instant wins to initial state"""
    db_path = project_root / 'data' / 'wildrandom.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # Reset instant win states
        cur.execute("""
            UPDATE instant_wins 
            SET status = 'allocated', 
                discovered_at = NULL,
                claim_deadline = NULL
            WHERE raffle_id = 1
        """)
        
        # Reset ticket states
        cur.execute("""
            UPDATE tickets 
            SET status = 'available',
                user_id = NULL,
                purchase_time = NULL
            WHERE raffle_id = 1
        """)
        
        conn.commit()
    finally:
        conn.close()

def test_instant_win_service():
    """Test InstantWin service functionality"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    
    with app.app_context():
        try:
            # Reset states first
            reset_instant_wins()
            print("Reset instant wins to initial state")
            
            # Get our existing raffle using session.get
            raffle = db.session.get(Raffle, 1)
            print(f"\nTesting with Raffle: {raffle.title}")
            
            # Update raffle to active if needed
            if raffle.status != RaffleStatus.ACTIVE.value:
                raffle.status = RaffleStatus.ACTIVE.value
                db.session.commit()
                print("Raffle status updated to active")
            
            # Try to purchase each instant win ticket
            winning_tickets = Ticket.query.filter_by(
                raffle_id=1,
                instant_win=True
            ).all()
            
            print("\nTesting Instant Win Purchase Flow:")
            for ticket in winning_tickets:
                print(f"\nProcessing ticket {ticket.ticket_id}:")
                
                # Verify initial state
                instant_win = InstantWin.query.filter_by(ticket_id=ticket.id).first()
                print(f"Initial InstantWin status: {instant_win.status}")
                
                # Simulate purchase
                print("Purchasing ticket...")
                ticket.status = TicketStatus.SOLD.value
                ticket.user_id = 1  # Admin user
                ticket.purchase_time = datetime.now(timezone.utc)
                db.session.commit()
                
                # Check for instant win
                instant_win, error = InstantWinService.check_instant_win(ticket.id)
                if error:
                    print(f"Error checking instant win: {error}")
                elif instant_win:
                    print(f"✓ Instant win detected and updated to: {instant_win.status}")
                    print(f"Prize Reference: {instant_win.prize_reference}")
                    
                    # Try to initiate claim
                    claim_info, error = InstantWinService.initiate_claim(instant_win.id, 1)
                    if error:
                        print(f"Error initiating claim: {error}")
                    else:
                        print("✓ Claim initiated")
                        print(f"Final status: {instant_win.status}")
                        print(f"Claim deadline: {claim_info['claim_deadline']}")
            
            print("\nFinal Statistics:")
            for status in InstantWinStatus:
                count = InstantWin.query.filter_by(
                    raffle_id=1,
                    status=status.value
                ).count()
                print(f"{status.value}: {count}")
            
        except Exception as e:
            print(f"Test failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    test_instant_win_service()