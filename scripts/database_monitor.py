# scripts/database_monitor.py
from pathlib import Path
import sys
from datetime import datetime, timezone
import sqlite3
from tabulate import tabulate

# Fix the project root path resolution
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def format_datetime(dt_str):
    """Format datetime string for display"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_str

def monitor_database():
    """Monitor database tables and display statistics"""
    # Updated database path resolution
    db_path = project_root / 'data' / 'wildrandom.db'
    
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        print("Please ensure you've initialized the database using:")
        print("python scripts/create_db.py")
        return
        
    print(f"Using database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # 1. Raffle Statistics
        print("\n=== Raffle Statistics ===")
        cur.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                MIN(created_at) as earliest,
                MAX(created_at) as latest,
                AVG(ticket_price) as avg_price,
                AVG(total_tickets) as avg_tickets
            FROM raffles
            GROUP BY status
        """)
        
        headers = ['Status', 'Count', 'Earliest', 'Latest', 'Avg Price', 'Avg Tickets']
        raffle_data = [[
            row[0],
            row[1],
            format_datetime(row[2]),
            format_datetime(row[3]),
            f"${row[4]:.2f}" if row[4] else "N/A",
            f"{row[5]:.0f}" if row[5] else "N/A"
        ] for row in cur.fetchall()]
        
        print(tabulate(raffle_data, headers=headers, tablefmt='grid'))
        
        # 2. Ticket Statistics
        print("\n=== Ticket Statistics ===")
        cur.execute("""
            SELECT 
                r.title as raffle_name,
                t.status,
                COUNT(*) as count,
                SUM(CASE WHEN t.instant_win = 1 THEN 1 ELSE 0 END) as instant_wins,
                COUNT(DISTINCT t.user_id) as unique_users
            FROM tickets t
            JOIN raffles r ON t.raffle_id = r.id
            GROUP BY r.title, t.status
        """)
        
        headers = ['Raffle', 'Status', 'Count', 'Instant Wins', 'Unique Users']
        ticket_data = [[
            row[0] if row[0] else "N/A",
            row[1],
            row[2],
            row[3],
            row[4]
        ] for row in cur.fetchall()]
        
        print(tabulate(ticket_data, headers=headers, tablefmt='grid'))
        
        # 3. Instant Win Statistics
        print("\n=== Instant Win Statistics ===")
        cur.execute("""
            SELECT 
                r.title as raffle_name,
                iw.status,
                COUNT(*) as count,
                MIN(iw.created_at) as earliest,
                MAX(iw.discovered_at) as latest_discovery
            FROM instant_wins iw
            JOIN raffles r ON iw.raffle_id = r.id
            GROUP BY r.title, iw.status
        """)
        
        headers = ['Raffle', 'Status', 'Count', 'Created', 'Last Discovery']
        instant_win_data = [[
            row[0] if row[0] else "N/A",
            row[1],
            row[2],
            format_datetime(row[3]),
            format_datetime(row[4])
        ] for row in cur.fetchall()]
        
        print(tabulate(instant_win_data, headers=headers, tablefmt='grid'))
        
        # Summary
        print("\n=== System Summary ===")
        summary = []
        
        # Total raffles
        cur.execute("SELECT COUNT(*) FROM raffles")
        total_raffles = cur.fetchone()[0]
        summary.append(['Total Raffles', total_raffles])
        
        # Total tickets
        cur.execute("SELECT COUNT(*) FROM tickets")
        total_tickets = cur.fetchone()[0]
        summary.append(['Total Tickets', total_tickets])
        
        # Total instant wins
        cur.execute("SELECT COUNT(*) FROM instant_wins")
        total_instant_wins = cur.fetchone()[0]
        summary.append(['Total Instant Wins', total_instant_wins])
        
        # Active users
        cur.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = cur.fetchone()[0]
        summary.append(['Active Users', active_users])
        
        print(tabulate(summary, headers=['Metric', 'Count'], tablefmt='grid'))
        
    except Exception as e:
        print(f"Error monitoring database: {e}")
        print(f"Exception details: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    monitor_database()