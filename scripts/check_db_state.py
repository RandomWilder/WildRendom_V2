# scripts/check_db_state.py
import logging
from pathlib import Path
import sqlite3
from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_db_state():
    """Check database and migration state"""
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'data' / 'wildrandom.db'
    
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # 1. Check alembic version
        logger.info("\nChecking alembic_version table:")
        cur.execute("SELECT * FROM alembic_version")
        version_data = cur.fetchall()
        print(tabulate(version_data, headers=['version_num'], tablefmt='grid'))
        
        # 2. Check table structure
        logger.info("\nChecking table structure:")
        table_info = []
        for table in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            table_name = table[0]
            count = cur.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            table_info.append([table_name, count])
        
        print(tabulate(table_info, headers=['Table', 'Row Count'], tablefmt='grid'))
        
        # 3. Check migrations directory
        migrations_dir = project_root / 'migrations'
        if migrations_dir.exists():
            logger.info("\nExisting migration files:")
            for file in migrations_dir.rglob('*.py'):
                print(f"- {file.relative_to(project_root)}")
        else:
            logger.info("\nNo migrations directory found")
            
    except Exception as e:
        logger.error(f"Error checking database state: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_db_state()