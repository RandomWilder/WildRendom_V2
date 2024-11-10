# scripts/migrate_prize_pools.py

from pathlib import Path
import sqlite3

def add_monitoring_columns():
    """Add monitoring columns safely to prize_pools"""
    conn = sqlite3.connect('data/wildrandom.db')
    cur = conn.cursor()
    
    try:
        existing_columns = [col[1] for col in cur.execute('PRAGMA table_info(prize_pools)').fetchall()]
        
        if 'peak_concurrent_claims' not in existing_columns:
            cur.execute('ALTER TABLE prize_pools ADD COLUMN peak_concurrent_claims INTEGER DEFAULT 0')
            
        if 'average_claim_time' not in existing_columns:
            cur.execute('ALTER TABLE prize_pools ADD COLUMN average_claim_time FLOAT DEFAULT 0.0')
            
        if 'total_forfeited' not in existing_columns:
            cur.execute('ALTER TABLE prize_pools ADD COLUMN total_forfeited INTEGER DEFAULT 0')
            
        conn.commit()
        print("Successfully added monitoring columns")
        
    except sqlite3.Error as e:
        print(f"Error adding columns: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_monitoring_columns()