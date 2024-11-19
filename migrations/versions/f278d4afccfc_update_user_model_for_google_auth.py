# migrations/versions/f278d4afccfc_update_user_model_for_google_auth.py

"""update user model for google auth

Revision ID: f278d4afccfc
Revises: head
Create Date: 2024-11-18 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = 'f278d4afccfc'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    
    # Create new table with desired schema
    conn.execute("""
        CREATE TABLE users_new (
            id INTEGER NOT NULL PRIMARY KEY,
            username VARCHAR(64) NOT NULL,
            email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(255) NULL,
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
    
    # Copy data from old table
    conn.execute("""
        INSERT INTO users_new 
        SELECT id, username, email, password_hash, first_name, last_name,
               site_credits, is_active, is_verified, is_admin, created_at,
               last_login, phone_number, auth_provider, google_id
        FROM users
    """)
    
    # Drop old table and constraints
    conn.execute("DROP TABLE users")
    
    # Rename new table
    conn.execute("ALTER TABLE users_new RENAME TO users")
    
    # Recreate indexes
    conn.execute("CREATE INDEX ix_users_username ON users (username)")
    conn.execute("CREATE INDEX ix_users_email ON users (email)")

def downgrade():
    conn = op.get_bind()
    
    # Create original table structure
    conn.execute("""
        CREATE TABLE users_old (
            id INTEGER NOT NULL PRIMARY KEY,
            username VARCHAR(64) NOT NULL,
            email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(64),
            last_name VARCHAR(64),
            site_credits FLOAT DEFAULT 0.0,
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 0,
            is_admin BOOLEAN DEFAULT 0 NOT NULL,
            created_at DATETIME,
            last_login DATETIME,
            phone_number VARCHAR(20),
            auth_provider VARCHAR(20) DEFAULT 'local',
            google_id VARCHAR(100)
        )
    """)
    
    # Copy data back
    conn.execute("""
        INSERT INTO users_old 
        SELECT id, username, email, COALESCE(password_hash, ''), first_name,
               last_name, site_credits, is_active, is_verified, is_admin,
               created_at, last_login, phone_number, auth_provider, google_id
        FROM users
    """)
    
    # Drop new table
    conn.execute("DROP TABLE users")
    
    # Rename old table back
    conn.execute("ALTER TABLE users_old RENAME TO users")
    
    # Recreate indexes
    conn.execute("CREATE INDEX ix_users_username ON users (username)")
    conn.execute("CREATE INDEX ix_users_email ON users (email)")