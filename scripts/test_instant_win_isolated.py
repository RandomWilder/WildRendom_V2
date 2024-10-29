# scripts/test_instant_win_isolated.py

from pathlib import Path
import sys
from datetime import datetime, timezone, timedelta
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db
from src.shared.config import config

def test_instant_win_setup():
    """Test InstantWin functionality setup with direct database access"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    
    with app.app_context():
        try:
            # Direct SQL approach to avoid import issues
            conn = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            cur = conn.cursor()
            
            # Create test raffle
            cur.execute("""
                INSERT INTO raffles (
                    title, description, total_tickets, ticket_price,
                    start_time, end_time, status, created_by_id,
                    instant_win_count, total_prize_count, max_tickets_per_user
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Test Raffle", "Testing InstantWin", 100, 10.0,
                datetime.now(timezone.utc).isoformat(),
                (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                'draft', 1, 5, 5, 10
            ))
            
            raffle_id = cur.lastrowid
            print(f"Created test raffle with ID: {raffle_id}")
            
            # Create tickets
            print("Creating tickets...")
            for i in range(100):
                ticket_number = str(i+1).zfill(3)
                ticket_id = f"{raffle_id}-{ticket_number}"
                cur.execute("""
                    INSERT INTO tickets (
                        raffle_id, ticket_id, ticket_number,
                        status, instant_win, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    raffle_id, ticket_id, ticket_number,
                    'available', False, datetime.now(timezone.utc).isoformat()
                ))
            
            # Select 5 random tickets for instant wins
            cur.execute("""
                SELECT id FROM tickets 
                WHERE raffle_id = ? AND status = 'available' 
                ORDER BY RANDOM() LIMIT 5
            """, (raffle_id,))
            
            winning_ticket_ids = cur.fetchall()
            
            # Create instant win entries
            for ticket_id in winning_ticket_ids:
                cur.execute("""
                    INSERT INTO instant_wins (
                        raffle_id, ticket_id, prize_reference,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    raffle_id, ticket_id[0],
                    f"test_prize_{raffle_id}_{ticket_id[0]}",
                    'allocated',
                    datetime.now(timezone.utc).isoformat()
                ))
                
                # Mark ticket as instant win
                cur.execute("""
                    UPDATE tickets 
                    SET instant_win = TRUE 
                    WHERE id = ?
                """, (ticket_id[0],))
            
            conn.commit()
            
            # Verify results
            cur.execute("SELECT COUNT(*) FROM instant_wins WHERE raffle_id = ?", (raffle_id,))
            instant_win_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM tickets WHERE raffle_id = ? AND instant_win = TRUE", (raffle_id,))
            marked_tickets_count = cur.fetchone()[0]
            
            print(f"InstantWin records created: {instant_win_count}")
            print(f"Tickets marked as instant wins: {marked_tickets_count}")
            
            conn.close()
            
        except Exception as e:
            print(f"Test failed: {str(e)}")
            conn.rollback()
            conn.close()
            raise

if __name__ == "__main__":
    test_instant_win_setup()
    