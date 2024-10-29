# scripts/inspect_db.py

from pathlib import Path
import sys
import sqlite3
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import config

def inspect_database():
    """Inspect the instant wins setup in detail"""
    db_path = project_root / 'data' / 'wildrandom.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # Get all raffles
        print("\n=== Raffles ===")
        cur.execute("""
            SELECT id, title, total_tickets, instant_win_count, status 
            FROM raffles
        """)
        raffles = cur.fetchall()
        for raffle in raffles:
            print(f"\nRaffle {raffle[0]}: {raffle[1]}")
            print(f"Total Tickets: {raffle[2]}")
            print(f"Instant Win Count: {raffle[3]}")
            print(f"Status: {raffle[4]}")
            
            # Get instant win tickets for this raffle
            print("\n--- Instant Win Tickets ---")
            cur.execute("""
                SELECT t.ticket_id, t.status, iw.status, iw.prize_reference
                FROM tickets t
                JOIN instant_wins iw ON t.id = iw.ticket_id
                WHERE t.raffle_id = ? AND t.instant_win = TRUE
            """, (raffle[0],))
            
            instant_wins = cur.fetchall()
            for win in instant_wins:
                print(f"\nTicket ID: {win[0]}")
                print(f"Ticket Status: {win[1]}")
                print(f"InstantWin Status: {win[2]}")
                print(f"Prize Reference: {win[3]}")
            
            # Get distribution statistics
            cur.execute("""
                SELECT COUNT(*) 
                FROM tickets 
                WHERE raffle_id = ? AND instant_win = TRUE
            """, (raffle[0],))
            win_count = cur.fetchone()[0]
            
            print(f"\n--- Statistics for Raffle {raffle[0]} ---")
            print(f"Total Instant Win Tickets: {win_count}")
            
    except Exception as e:
        print(f"Error inspecting database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_database()