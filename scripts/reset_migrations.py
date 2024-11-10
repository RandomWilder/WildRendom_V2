# scripts/reset_migrations.py

from pathlib import Path
import sys
import sqlite3
import shutil
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_migrations():
    """Reset the migration state and clean up database"""
    # 1. Handle migrations folder
    migrations_dir = project_root / 'migrations'
    if migrations_dir.exists():
        logger.info("Removing migrations directory...")
        shutil.rmtree(migrations_dir)
        logger.info("Migrations directory removed.")

    # 2. Handle database
    db_path = project_root / 'data' / 'wildrandom.db'
    
    if db_path.exists():
        try:
            logger.info("Connecting to database...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get list of all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Drop alembic version table if exists
            logger.info("Cleaning up alembic version...")
            cursor.execute("DROP TABLE IF EXISTS alembic_version;")
            
            conn.commit()
            logger.info("Successfully reset migration state.")
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
        finally:
            conn.close()
    else:
        logger.info(f"No existing database found at {db_path}")
        
    # 3. Create data directory if it doesn't exist
    db_path.parent.mkdir(exist_ok=True)
    
    logger.info("Migration reset complete. You can now run:")
    logger.info("1. flask db init")
    logger.info("2. flask db migrate -m 'Initial migration'")
    logger.info("3. flask db upgrade")

if __name__ == "__main__":
    try:
        reset_migrations()
    except Exception as e:
        logger.error(f"Error during reset: {e}")
        sys.exit(1)