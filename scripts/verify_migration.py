# scripts/verify_migration.py
import logging
from pathlib import Path
import sqlite3
from tabulate import tabulate
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_database():
    """Verify database state after migration"""
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'data' / 'wildrandom.db'
    
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # 1. Check migration version
        logger.info("\nMigration Status:")
        cur.execute("SELECT version_num FROM alembic_version")
        version_data = cur.fetchall()
        print(tabulate(version_data, headers=['Current Version'], tablefmt='grid'))
        
        # 2. Check all tables and their row counts
        logger.info("\nTable Status:")
        # Define expected tables with their expected minimum row counts
        expected_tables = {
            'users': 1,
            'raffles': 1,
            'tickets': 1,
            'prize_pools': 1,
            'prizes': 1,
            'credit_transactions': 0,
            'user_activities': 0,
            'user_raffle_stats': 0,
            'instant_wins': 0,
            'prize_instances': 0,
            'prize_allocations': 0,
            'raffle_status_changes': 0,
            'user_status_changes': 0,
            # New tables
            'ticket_reservations': 0,
            'reserved_tickets': 0
        }
        
        table_status = []
        all_tables = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sqlite_sequence', 'alembic_version')"
        ).fetchall()
        
        for table in all_tables:
            table_name = table[0]
            count = cur.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            expected_min = expected_tables.get(table_name, 0)
            status = "✓" if count >= expected_min else "!"
            
            # Get creation SQL for structure verification
            create_sql = cur.execute(
                f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", 
                (table_name,)
            ).fetchone()[0]
            
            table_status.append([
                status,
                table_name,
                count,
                "New" if table_name in ['ticket_reservations', 'reserved_tickets'] else "Existing"
            ])
        
        print(tabulate(
            table_status,
            headers=['Status', 'Table', 'Row Count', 'Type'],
            tablefmt='grid'
        ))
        
        # 3. Verify foreign key constraints
        logger.info("\nVerifying Foreign Key Constraints:")
        cur.execute("PRAGMA foreign_key_check")
        fk_violations = cur.fetchall()
        if not fk_violations:
            print("✓ All foreign key constraints are valid")
        else:
            print("! Foreign key violations found:", fk_violations)
        
        # 4. Verify new table structure
        logger.info("\nNew Tables Structure:")
        new_tables = ['ticket_reservations', 'reserved_tickets']
        for table in new_tables:
            print(f"\n{table} columns:")
            columns = cur.execute(f"PRAGMA table_info({table})").fetchall()
            column_info = [[col[1], col[2], "NOT NULL" if col[3] else "NULL"] for col in columns]
            print(tabulate(column_info, headers=['Column', 'Type', 'Nullable'], tablefmt='grid'))
            
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_database()