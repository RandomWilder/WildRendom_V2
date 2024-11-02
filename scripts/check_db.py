# scripts/check_db.py

from pathlib import Path
import sys
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_db():
    """Check database structure"""
    db_path = project_root / 'data' / 'wildrandom.db'
    
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Existing tables:")
    for table in tables:
        print(f"- {table[0]}")
        # Get table structure
        cursor.execute(f"PRAGMA table_info({table[0]});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_db()