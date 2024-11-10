# scripts/add_monitoring_indices.py

from pathlib import Path
import sqlite3

def add_monitoring_indices():
    """Add performance indices for monitoring"""
    conn = sqlite3.connect('data/wildrandom.db')
    cur = conn.cursor()
    
    try:
        # Add prize_pools indices
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_pool_status_monitoring 
            ON prize_pools(status, start_date)
        ''')
        
        # Add prize_allocations indices
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_allocation_monitoring 
            ON prize_allocations(pool_id, claim_status, claimed_at)
        ''')
        
        # Add compound index for time-based queries
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_allocation_timing 
            ON prize_allocations(claim_status, claimed_at, pool_id)
        ''')
        
        conn.commit()
        print("Successfully added monitoring indices")
        
    except sqlite3.Error as e:
        print(f"Error adding indices: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_monitoring_indices()