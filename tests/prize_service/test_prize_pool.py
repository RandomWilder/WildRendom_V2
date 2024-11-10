# tests/prize_service/test_prize_pool.py

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from src.prize_service.models import PrizePool, PoolStatus
from src.prize_service.services.prize_service import PrizeService

@pytest.fixture
def sample_pool_data():
    return {
        'name': 'Test Pool',
        'description': 'Test Description',
        'start_date': datetime.now(timezone.utc),
        'end_date': datetime.now(timezone.utc) + timedelta(days=7),
        'budget_limit': Decimal('1000.00')
    }

@pytest.fixture
def sample_allocation_data():
    return {
        'prize_template_id': 1,
        'instance_count': 10,
        'collective_odds': 70.0
    }

@pytest.fixture
def created_pool(sample_pool_data, db_session):
    pool, _ = PrizeService.create_pool(sample_pool_data, admin_id=1)
    return pool

class TestPoolCreation:
    def test_create_pool(self, db_session, sample_pool_data):
        """Test pool creation"""
        pool, error = PrizeService.create_pool(sample_pool_data, admin_id=1)
        
        assert error is None
        assert pool is not None
        assert pool.name == sample_pool_data['name']
        assert pool.status == PoolStatus.UNLOCKED.value
        assert pool.total_prizes == 0

    def test_create_pool_invalid_dates(self, db_session, sample_pool_data):
        """Test pool creation with invalid dates"""
        sample_pool_data['end_date'] = sample_pool_data['start_date']
        pool, error = PrizeService.create_pool(sample_pool_data, admin_id=1)
        
        assert error is not None
        assert 'end_date must be after start_date' in error

class TestPrizeAllocation:
    def test_allocate_prizes(self, db_session, created_pool, sample_allocation_data, test_prizes):
        """Test prize allocation to pool"""
        allocation, error = PrizeService.allocate_to_pool(
            pool_id=created_pool.id,
            prize_id=test_prizes[0].id,  # Use actual prize from fixture
            quantity=sample_allocation_data['instance_count'],
            collective_odds=sample_allocation_data['collective_odds'],
            admin_id=1
        )
        
        assert error is None
        assert allocation is not None
        assert len(allocation['allocated_instances']) == sample_allocation_data['instance_count']
        assert allocation['pool_updated_totals']['total_instances'] == sample_allocation_data['instance_count']

    def test_allocate_prizes_locked_pool(self, db_session, created_pool, sample_allocation_data):
        """Test allocation to locked pool"""
        created_pool.status = PoolStatus.LOCKED.value
        db_session.session.commit()
        
        allocation, error = PrizeService.allocate_to_pool(
            pool_id=created_pool.id,
            prize_id=sample_allocation_data['prize_template_id'],
            quantity=sample_allocation_data['instance_count'],
            collective_odds=sample_allocation_data['collective_odds'],
            admin_id=1
        )
        
        assert error is not None
        assert 'Can only allocate to UNLOCKED pools' in error

    def test_allocate_invalid_odds(self, db_session, created_pool, test_prizes):
        """Test allocation with invalid collective odds"""
        allocation, error = PrizeService.allocate_to_pool(
            pool_id=created_pool.id,
            prize_id=test_prizes[0].id,
            quantity=10,
            collective_odds=101.0,  # Invalid odds
            admin_id=1
        )
        
        assert error is not None
        assert 'collective_odds' in error.lower()

class TestPoolLocking:
    def test_lock_pool_valid(self, db_session, created_pool, test_prizes):
        """Test locking pool with valid configuration"""
        # First allocate required prizes
        PrizeService.allocate_to_pool(
            pool_id=created_pool.id,
            prize_id=test_prizes[0].id,  # Draw_Win prize
            quantity=1,
            collective_odds=30.0,
            admin_id=1
        )
        
        PrizeService.allocate_to_pool(
            pool_id=created_pool.id,
            prize_id=test_prizes[1].id,  # Instant_Win prize
            quantity=10,
            collective_odds=70.0,
            admin_id=1
        )
        
        validation, error = PrizeService.lock_pool(created_pool.id, admin_id=1)
        
        assert error is None
        assert validation['has_instances'] is True
        assert validation['has_draw_win'] is True
        assert abs(validation['odds_total'] - 100.0) < 0.0001

    def test_lock_pool_without_draw_win(self, db_session, created_pool, test_prizes):
        """Test locking pool without required Draw_Win prize"""
        # Allocate only Instant_Win prizes
        PrizeService.allocate_to_pool(
            pool_id=created_pool.id,
            prize_id=test_prizes[1].id,  # Instant_Win prize
            quantity=10,
            collective_odds=100.0,
            admin_id=1
        )
        
        validation, error = PrizeService.lock_pool(created_pool.id, admin_id=1)
        
        assert error is not None
        assert 'Must have at least one Draw Win prize' in error

    def test_lock_pool_invalid_odds_total(self, db_session, created_pool, test_prizes):
        """Test locking pool with invalid odds total"""
        PrizeService.allocate_to_pool(
            pool_id=created_pool.id,
            prize_id=test_prizes[0].id,
            quantity=1,
            collective_odds=50.0,  # Total odds will be less than 100
            admin_id=1
        )
        
        validation, error = PrizeService.lock_pool(created_pool.id, admin_id=1)
        
        assert error is not None
        assert validation['odds_total'] < 100.0

class TestPoolTransitions:
    def test_unlock_pool_valid(self, db_session, created_pool):
        """Test unlocking a locked pool"""
        created_pool.status = PoolStatus.LOCKED.value
        db_session.session.commit()
        
        result, error = PrizeService.unlock_pool(created_pool.id, admin_id=1)
        
        assert error is None
        assert result['status'] == PoolStatus.UNLOCKED.value

    def test_unlock_used_pool(self, db_session, created_pool):
        """Test unlocking attempt on USED pool"""
        created_pool.status = PoolStatus.USED.value
        db_session.session.commit()
        
        result, error = PrizeService.unlock_pool(created_pool.id, admin_id=1)
        
        assert error is not None
        assert 'Can only unlock LOCKED pools' in error

class TestPoolStats:
    def test_get_pool_stats(self, db_session, created_pool, test_prizes):
        """Test pool statistics calculation"""
        # Allocate mixed prize types
        PrizeService.allocate_to_pool(
            pool_id=created_pool.id,
            prize_id=test_prizes[0].id,
            quantity=1,
            collective_odds=30.0,
            admin_id=1
        )
        
        PrizeService.allocate_to_pool(
            pool_id=created_pool.id,
            prize_id=test_prizes[1].id,
            quantity=5,
            collective_odds=70.0,
            admin_id=1
        )
        
        stats, error = PrizeService.get_pool_stats(created_pool.id)
        
        assert error is None
        assert stats['total_instances'] == 6
        assert stats['by_type']['draw_win']['total'] == 1
        assert stats['by_type']['instant_win']['total'] == 5

    def test_get_pool_claim_stats(self, db_session, created_pool):
        """Test pool claim statistics"""
        stats, error = PrizeService.get_pool_claim_stats(created_pool.id)
        
        assert error is None
        assert stats is not None
        assert 'total_instances' in stats
        assert 'by_type' in stats
        assert 'values_claimed' in stats