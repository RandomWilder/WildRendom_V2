import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / 'data' / 'wildrandom.db'

restore_tables_sql = """
-- Raffles table
CREATE TABLE IF NOT EXISTS raffles (
    id INTEGER PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    total_tickets INTEGER NOT NULL,
    ticket_price FLOAT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL,
    max_tickets_per_user INTEGER NOT NULL,
    total_prize_count INTEGER NOT NULL,
    instant_win_count INTEGER,
    prize_structure JSON,
    created_at DATETIME,
    created_by_id INTEGER NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY(created_by_id) REFERENCES users(id)
);

-- User Activities table
CREATE TABLE IF NOT EXISTS user_activities (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    status VARCHAR(20),
    details JSON,
    created_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Raffle Status Changes table
CREATE TABLE IF NOT EXISTS raffle_status_changes (
    id INTEGER PRIMARY KEY,
    raffle_id INTEGER NOT NULL,
    previous_status VARCHAR(20) NOT NULL,
    new_status VARCHAR(20) NOT NULL,
    changed_by_id INTEGER NOT NULL,
    reason VARCHAR(255),
    created_at DATETIME,
    FOREIGN KEY(raffle_id) REFERENCES raffles(id),
    FOREIGN KEY(changed_by_id) REFERENCES users(id)
);

-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    raffle_id INTEGER NOT NULL,
    ticket_id VARCHAR(20) NOT NULL UNIQUE,
    ticket_number VARCHAR(3) NOT NULL,
    user_id INTEGER,
    purchase_time DATETIME,
    status VARCHAR(20) NOT NULL,
    is_revealed BOOLEAN,
    reveal_time DATETIME,
    reveal_sequence INTEGER,
    instant_win BOOLEAN,
    instant_win_eligible BOOLEAN,
    transaction_id INTEGER,
    created_at DATETIME,
    FOREIGN KEY(raffle_id) REFERENCES raffles(id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(transaction_id) REFERENCES credit_transactions(id)
);

-- Create ticket indices
CREATE INDEX IF NOT EXISTS idx_ticket_id ON tickets(ticket_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ticket_raffle_number ON tickets(raffle_id, ticket_number);
CREATE INDEX IF NOT EXISTS idx_ticket_reveal ON tickets(raffle_id, user_id, reveal_time);

-- Instant Wins table
CREATE TABLE IF NOT EXISTS instant_wins (
    id INTEGER PRIMARY KEY,
    raffle_id INTEGER NOT NULL,
    ticket_id INTEGER NOT NULL,
    prize_reference VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    discovered_at DATETIME,
    claim_deadline DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(raffle_id) REFERENCES raffles(id) ON DELETE RESTRICT,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE RESTRICT,
    CONSTRAINT uq_one_win_per_ticket UNIQUE (ticket_id)
);

CREATE INDEX IF NOT EXISTS ix_instant_wins_raffle_id_status ON instant_wins(raffle_id, status);

-- Prize Pools table
CREATE TABLE IF NOT EXISTS prize_pools (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL,
    allocation_strategy VARCHAR(20) NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    odds_configuration JSON,
    total_prizes INTEGER,
    available_prizes INTEGER,
    budget_limit NUMERIC(10,2),
    current_allocation NUMERIC(10,2),
    total_value NUMERIC(10,2),
    win_limits JSON,
    eligibility_rules JSON,
    created_at DATETIME,
    updated_at DATETIME,
    created_by_id INTEGER NOT NULL,
    instant_win_count INTEGER,
    draw_prize_count INTEGER,
    FOREIGN KEY(created_by_id) REFERENCES users(id)
);

-- Prizes table
CREATE TABLE IF NOT EXISTS prizes (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(20) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    tier_priority INTEGER,
    retail_value NUMERIC(10,2) NOT NULL,
    cash_value NUMERIC(10,2) NOT NULL,
    credit_value NUMERIC(10,2) NOT NULL,
    total_quantity INTEGER,
    available_quantity INTEGER,
    total_claimed INTEGER,
    win_limit_per_user INTEGER,
    win_limit_period_days INTEGER,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME,
    updated_at DATETIME,
    created_by_id INTEGER NOT NULL,
    win_odds FLOAT,
    total_allocated INTEGER,
    claim_deadline_hours INTEGER,
    auto_claim_credit BOOLEAN,
    FOREIGN KEY(created_by_id) REFERENCES users(id)
);

-- Prize Allocations table
CREATE TABLE IF NOT EXISTS prize_allocations (
    id INTEGER PRIMARY KEY,
    prize_id INTEGER NOT NULL,
    pool_id INTEGER NOT NULL,
    allocation_type VARCHAR(20) NOT NULL,
    reference_type VARCHAR(50) NOT NULL,
    reference_id VARCHAR(100) NOT NULL,
    winner_user_id INTEGER,
    won_at DATETIME,
    claim_status VARCHAR(20),
    claim_deadline DATETIME,
    claimed_at DATETIME,
    claim_method VARCHAR(20),
    value_claimed NUMERIC(10,2),
    allocation_config JSON,
    created_at DATETIME,
    updated_at DATETIME,
    created_by_id INTEGER NOT NULL,
    sequence_number INTEGER,
    winning_odds FLOAT,
    auto_claim_attempted BOOLEAN,
    original_value NUMERIC(10,2),
    verification_code VARCHAR(50),
    claim_ip_address VARCHAR(45),
    FOREIGN KEY(prize_id) REFERENCES prizes(id),
    FOREIGN KEY(pool_id) REFERENCES prize_pools(id),
    FOREIGN KEY(winner_user_id) REFERENCES users(id),
    FOREIGN KEY(created_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_allocation_reference ON prize_allocations(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_allocation_user ON prize_allocations(winner_user_id, claim_status);

-- User Raffle Stats table
CREATE TABLE IF NOT EXISTS user_raffle_stats (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    raffle_id INTEGER NOT NULL,
    tickets_purchased INTEGER,
    last_purchase_time DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(raffle_id) REFERENCES raffles(id),
    CONSTRAINT unique_user_raffle UNIQUE (user_id, raffle_id)
);
"""

def restore_tables():
    print("Starting database restoration...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.executescript(restore_tables_sql)
        conn.commit()
        print("Tables restored successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during restoration: {str(e)}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    restore_tables()