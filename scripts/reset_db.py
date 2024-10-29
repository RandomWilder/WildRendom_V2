# scripts/reset_db.py
from pathlib import Path
import sys
import os
import time
import psutil
import logging
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def kill_db_connections():
    """Kill processes that might be holding the database"""
    db_path = project_root / 'data' / 'wildrandom.db'
    
    # Try to close any open SQLite connections
    try:
        conn = sqlite3.connect(db_path)
        conn.close()
    except:
        pass

    # Look for Python processes that might be using the database
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and any('wildrandom' in str(cmd).lower() for cmd in cmdline):
                    if proc.pid != os.getpid():  # Don't kill ourselves
                        proc.terminate()
                        proc.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue

def reset_db():
    """Reset the database"""
    # Database path
    db_path = project_root / 'data' / 'wildrandom.db'
    
    if db_path.exists():
        print(f"Removing existing database: {db_path}")
        
        # Try to kill any processes using the database
        kill_db_connections()
        
        # Wait a moment for processes to terminate
        time.sleep(2)
        
        try:
            os.remove(db_path)
            print("Database file removed.")
        except PermissionError:
            print("Could not remove database file - please close any applications using it and try again.")
            print("You might need to manually close your Python/Flask application.")
            sys.exit(1)
    
    print("Initializing fresh database...")
    # Import and run init_db after database is removed
    from scripts.create_db import init_db
    init_db()

if __name__ == "__main__":
    reset_db()