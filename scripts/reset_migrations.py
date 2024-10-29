# scripts/reset_migrations.py

from pathlib import Path
import sys
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def reset_migrations():
    """Reset the database version control"""
    db_path = project_root / 'data' / 'wildrandom.db'
    
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Delete version control
        cursor.execute("DELETE FROM alembic_version;")
        conn.commit()
        print("Successfully reset migration version control.")
    except sqlite3.Error as e:
        print(f"Error resetting migrations: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_migrations()