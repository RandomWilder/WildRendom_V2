# scripts/update_sqlite_schema.py

import sqlite3
import logging
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_database():
    """Create backup of database"""
    try:
        src = 'data/wildrandom.db'
        dst = 'data/wildrandom.db.backup_schema'
        import shutil
        shutil.copy2(src, dst)
        logger.info(f"Created backup at {dst}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return False

def update_users_table():
    """Update users table schema to allow null password_hash"""
    if not backup_database():
        logger.error("Aborting due to backup failure")
        return False

    try:
        db_path = Path('data/wildrandom.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info("Starting schema update...")

        # Get existing data first
        cursor.execute("SELECT * FROM users")
        existing_data = cursor.fetchall()
        logger.info(f"Retrieved {len(existing_data)} existing user records")

        # Create new table with desired schema
        logger.info("Creating new table structure...")
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER NOT NULL PRIMARY KEY,
                username VARCHAR(64) NOT NULL,
                email VARCHAR(120) NOT NULL,
                password_hash VARCHAR(255),  -- Removed NOT NULL constraint
                first_name VARCHAR(64),
                last_name VARCHAR(64),
                site_credits FLOAT DEFAULT 0.0,
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 0,
                is_admin BOOLEAN DEFAULT 0 NOT NULL,
                created_at DATETIME,
                last_login DATETIME,
                phone_number VARCHAR(20) UNIQUE,
                auth_provider VARCHAR(20) DEFAULT 'local',
                google_id VARCHAR(100) UNIQUE
            )
        """)

        # Copy existing data
        logger.info("Copying existing data...")
        cursor.execute("""
            INSERT INTO users_new 
            SELECT * FROM users
        """)

        # Verify data copy
        cursor.execute("SELECT COUNT(*) FROM users_new")
        new_count = cursor.fetchone()[0]
        if new_count != len(existing_data):
            raise Exception(f"Data copy mismatch. Original: {len(existing_data)}, New: {new_count}")

        # Drop old table
        logger.info("Dropping old table...")
        cursor.execute("DROP TABLE users")

        # Rename new table to users
        logger.info("Renaming new table...")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        # Recreate indexes
        logger.info("Recreating indexes...")
        cursor.execute("CREATE INDEX ix_users_username ON users (username)")
        cursor.execute("CREATE INDEX ix_users_email ON users (email)")

        # Commit changes
        conn.commit()
        logger.info("Successfully updated users table schema")
        
        # Verify final state
        cursor.execute("SELECT COUNT(*) FROM users")
        final_count = cursor.fetchone()[0]
        logger.info(f"Final user count: {final_count}")
        
        return True

    except Exception as e:
        logger.error(f"Error updating schema: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    update_users_table()