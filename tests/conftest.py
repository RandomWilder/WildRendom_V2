# tests/conftest.py

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from src.shared import db
from src.prize_service.models import (
    Prize,
    PrizePool, 
    PrizeAllocation,
    AllocationType,
    ClaimStatus
)
from src.raffle_service.models import Raffle
from src.user_service.models import User
from flask import Flask
from src.shared.config import TestingConfig  # Changed from TestConfig to TestingConfig

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    db.init_app(app)
    return app

@pytest.fixture(scope='function')
def db_session(app):
    """Provide a clean database session for tests"""
    with app.app_context():
        db.create_all()  # Create all tables
        
        # Get session
        session = db.session
        
        yield session

        session.close()
        db.session.remove()
        db.drop_all()

@pytest.fixture
def admin_user(db_session):
    """Create admin user for testing"""
    user = User(
        username='admin',
        email='admin@test.com',
        is_admin=True,
        is_active=True
    )
    user.set_password('admin123')
    db_session.add(user)  # Changed from db_session.session.add
    db_session.commit()   # Changed from db_session.session.commit
    return user

@pytest.fixture
def test_prizes(db_session):
    """Create test prize templates"""
    prizes = []
    
    # Create Draw Win prize first
    draw_prize = Prize(
        name='Gold Draw Prize',
        type='Draw_Win',  # Make sure type matches exactly
        tier='gold',
        retail_value=Decimal('1000.00'),
        cash_value=Decimal('800.00'),
        credit_value=Decimal('900.00'),
        created_by_id=1
    )
    
    # Create Instant Win prize second
    instant_prize = Prize(
        name='Silver Instant Prize',
        type='Instant_Win',  # Make sure type matches exactly
        tier='silver',
        retail_value=Decimal('100.00'),
        cash_value=Decimal('80.00'),
        credit_value=Decimal('90.00'),
        created_by_id=1
    )
    
    prizes.extend([draw_prize, instant_prize])
    db_session.add_all(prizes)  # Changed from db_session.session.add_all
    db_session.commit()         # Changed from db_session.session.commit
    
    return prizes

@pytest.fixture
def test_pool(db_session):
    """Create test prize pool"""
    pool = PrizePool(
        name='Test Pool',
        description='Test Description',
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=7),
        created_by_id=1,
        instant_win_count=0,
        draw_win_count=0,
        total_instances=0,
        raffle_id=None  # Make it optional for tests
    )
    db_session.add(pool)  # Changed from db_session.session.add
    db_session.commit()   # Changed from db_session.session.commit
    return pool

@pytest.fixture
def test_allocation(db_session, test_pool, test_prizes):
    """Create test allocation"""
    allocation = PrizeAllocation(
        pool_id=test_pool.id,
        prize_id=test_prizes[0].id,
        allocation_type=AllocationType.INSTANT_WIN.value,
        reference_type='ticket',
        reference_id='TEST-001',
        claim_status=ClaimStatus.PENDING.value,
        created_by_id=1
    )
    db_session.add(allocation)  # Changed from db_session.session.add
    db_session.commit()         # Changed from db_session.session.commit
    return allocation

@pytest.fixture
def load_test_data(db_session, test_pool, test_prizes):
    """Create substantial test data for monitoring tests"""
    allocations = []
    timestamps = [
        datetime.now(timezone.utc) - timedelta(hours=i)
        for i in range(24)
    ]
    
    for i, timestamp in enumerate(timestamps):
        allocation = PrizeAllocation(
            pool_id=test_pool.id,
            prize_id=test_prizes[0].id,
            claim_status='claimed' if i % 2 == 0 else 'pending',
            claimed_at=timestamp if i % 2 == 0 else None,
            allocation_type='instant_win',
            created_by_id=1,
            created_at=timestamp
        )
        allocations.append(allocation)
    
    db_session.add_all(allocations)  # Changed from db_session.add_all
    db_session.commit()              # Changed from db_session.commit
    return allocations

@pytest.fixture
def test_raffle(db_session):
    """Create test raffle"""
    raffle = Raffle(
        title='Test Raffle',
        description='Test Description',
        total_tickets=100,
        ticket_price=10.0,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(days=7),
        status='draft',
        max_tickets_per_user=10,
        total_prize_count=0,
        instant_win_count=0,
        created_by_id=1
    )
    db_session.add(raffle)  # Changed from db_session.session.add
    db_session.commit()     # Changed from db_session.session.commit
    return raffle