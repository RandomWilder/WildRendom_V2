# tests/integration/test_raffle_integration.py

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from src.prize_service.models import Prize, PrizePool, PoolStatus
from src.raffle_service.models import Raffle, RaffleStatus
from src.user_service.models import User, CreditTransaction

# Define our common test data
TEST_PRIZE_DATA = {
    'name': 'Test Prize',
    'type': 'Instant_Win',
    'tier': 'silver',
    'retail_value': Decimal('100.00'),
    'cash_value': Decimal('80.00'),
    'credit_value': Decimal('90.00'),
    'status': 'active'
}

TEST_RAFFLE_DATA = {
    'title': 'Test Raffle',
    'description': 'Test Description',
    'total_tickets': 100,
    'ticket_price': 10.0,
    'max_tickets_per_user': 10,
    'draw_configuration': {
        'number_of_draws': 1,
        'distribution_type': 'single'
    }
}

@pytest.fixture(scope='function')
def setup_test_env(db_session, admin_user):
    """Setup test environment with necessary data"""
    # Create test prize
    prize = Prize(
        **TEST_PRIZE_DATA,
        created_by_id=admin_user.id
    )
    db_session.add(prize)
    
    # Create and lock prize pool
    pool = PrizePool(
        name="Test Pool",
        description="Test Description",
        status=PoolStatus.LOCKED.value,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=7),
        created_by_id=admin_user.id,
        instant_win_count=5,
        draw_win_count=1,
        total_instances=6,
        retail_total=Decimal('1000.00'),
        cash_total=Decimal('800.00'),
        credit_total=Decimal('900.00')
    )
    db_session.add(pool)
    db_session.commit()
    
    return {'prize': prize, 'pool': pool}

@pytest.fixture
def test_user_with_credits(db_session):
    """Create test user with sufficient credits"""
    user = User(
        username='test_buyer',
        email='buyer@test.com',
        site_credits=1000.0,
        is_active=True
    )
    user.set_password('Test123!@#')
    db_session.add(user)
    db_session.commit()
    return user

def test_create_raffle_with_prize_pool(client, setup_test_env, admin_user):
    """Test complete raffle creation flow with prize pool"""
    # Login as admin
    response = client.post('/api/users/login', json={
        'username': admin_user.username,
        'password': 'admin123'
    })
    assert response.status_code == 200
    admin_token = response.json['token']

    # Prepare raffle data
    raffle_data = TEST_RAFFLE_DATA.copy()
    raffle_data.update({
        'start_time': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        'end_time': (datetime.now(timezone.utc) + timedelta(days=8)).isoformat(),
        'prize_pool_id': setup_test_env['pool'].id
    })

    # Create raffle
    response = client.post(
        '/api/admin/raffles/create',
        json=raffle_data,
        headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == 201
    data = response.json

    # Verify response structure
    assert data['title'] == raffle_data['title']
    assert data['prize_pool_id'] == setup_test_env['pool'].id
    assert 'tickets' in data
    assert data['tickets']['total_generated'] == 100
    assert data['tickets']['instant_win_eligible'] == 5
    assert 'draw_configuration' in data
    assert data['draw_configuration']['number_of_draws'] == 1
    assert 'claim_deadlines' in data
    assert 'instant_win' in data['claim_deadlines']
    assert 'draw_win' in data['claim_deadlines']

def test_purchase_tickets_flow(client, setup_test_env, test_user_with_credits, admin_user):
    """Test complete ticket purchase flow"""
    # Login as test user
    response = client.post('/api/users/login', json={
        'username': test_user_with_credits.username,
        'password': 'Test123!@#'
    })
    assert response.status_code == 200
    user_token = response.json['token']

    # Create and activate raffle (as admin)
    response = client.post('/api/users/login', json={
        'username': admin_user.username,
        'password': 'admin123'
    })
    admin_token = response.json['token']

    # Create raffle
    raffle_data = TEST_RAFFLE_DATA.copy()
    raffle_data.update({
        'start_time': datetime.now(timezone.utc).isoformat(),
        'end_time': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        'prize_pool_id': setup_test_env['pool'].id
    })

    response = client.post(
        '/api/admin/raffles/create',
        json=raffle_data,
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 201
    raffle_id = response.json['id']

    # Activate raffle
    response = client.put(
        f'/api/admin/raffles/{raffle_id}/status',
        json={'status': 'active'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 200

    # Purchase tickets
    purchase_quantity = 5
    response = client.post(
        f'/api/raffles/{raffle_id}/tickets',
        json={'quantity': purchase_quantity},
        headers={'Authorization': f'Bearer {user_token}'}
    )

    assert response.status_code == 201
    data = response.json

    # Verify response structure
    assert 'tickets' in data
    assert len(data['tickets']) == purchase_quantity
    assert 'transaction' in data
    assert data['transaction']['amount'] == purchase_quantity * TEST_RAFFLE_DATA['ticket_price']
    
    # Verify tickets exist in database
    ticket_ids = [t['ticket_id'] for t in data['tickets']]
    for ticket_id in ticket_ids:
        response = client.get(
            f'/api/raffles/{raffle_id}/tickets/{ticket_id}',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200

def test_invalid_raffle_creation(client, setup_test_env, admin_user):
    """Test validation errors during raffle creation"""
    # Login as admin
    response = client.post('/api/users/login', json={
        'username': admin_user.username,
        'password': 'admin123'
    })
    admin_token = response.json['token']

    # Test case 1: End time before start time
    raffle_data = TEST_RAFFLE_DATA.copy()
    raffle_data.update({
        'start_time': (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        'end_time': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        'prize_pool_id': setup_test_env['pool'].id
    })

    response = client.post(
        '/api/admin/raffles/create',
        json=raffle_data,
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 400
    assert 'End time must be after start time' in str(response.json['error'])

    # Test case 2: Invalid prize pool ID
    raffle_data.update({
        'end_time': (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        'prize_pool_id': 99999  # Non-existent pool
    })

    response = client.post(
        '/api/admin/raffles/create',
        json=raffle_data,
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 400
    assert 'Prize pool not found' in str(response.json['error'])

    # Test case 3: Invalid draw configuration
    raffle_data.update({
        'prize_pool_id': setup_test_env['pool'].id,
        'draw_configuration': {
            'number_of_draws': 0,  # Invalid
            'distribution_type': 'single'
        }
    })

    response = client.post(
        '/api/admin/raffles/create',
        json=raffle_data,
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 400
    assert 'Number of draws must be at least 1' in str(response.json['error'])