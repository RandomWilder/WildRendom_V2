# tests/prize_service/test_prize_service.py

import pytest
from datetime import datetime, timezone, timedelta
from src.prize_service.models import Prize, PrizeStatus, PrizeTier, PrizeInstance, InstanceStatus
from src.prize_service.services.prize_service import PrizeService
from decimal import Decimal

@pytest.fixture
def sample_prize_data():
    return {
        'name': 'Test Prize',
        'description': 'Test Description',
        'type': 'Instant_Win',
        'tier': 'silver',
        'retail_value': Decimal('100.00'),
        'cash_value': Decimal('80.00'),
        'credit_value': Decimal('90.00'),
        'expiry_days': 7
    }

@pytest.fixture
def created_prize(sample_prize_data, db_session):
    prize, _ = PrizeService.create_prize(sample_prize_data, admin_id=1)
    return prize

class TestPrizeTemplateManagement:
    def test_create_prize(self, db_session, sample_prize_data):
        """Test prize template creation"""
        prize, error = PrizeService.create_prize(sample_prize_data, admin_id=1)
        
        assert error is None
        assert prize is not None
        assert prize.name == sample_prize_data['name']
        assert prize.type == sample_prize_data['type']
        assert prize.tier == sample_prize_data['tier']
        assert prize.retail_value == sample_prize_data['retail_value']
        assert prize.status == PrizeStatus.ACTIVE.value

    def test_create_prize_invalid_type(self, db_session, sample_prize_data):
        """Test prize creation with invalid type"""
        sample_prize_data['type'] = 'invalid_type'
        prize, error = PrizeService.create_prize(sample_prize_data, admin_id=1)
        
        assert error is not None
        assert prize is None

    def test_update_prize(self, db_session, created_prize):
        """Test prize template update"""
        update_data = {
            'name': 'Updated Prize',
            'retail_value': Decimal('110.00')
        }
        
        updated_prize, error = PrizeService.update_prize(
            prize_id=created_prize.id,
            data=update_data,
            admin_id=1
        )
        
        assert error is None
        assert updated_prize.name == update_data['name']
        assert updated_prize.retail_value == update_data['retail_value']
        assert updated_prize.updated_at is not None

    def test_update_used_prize(self, db_session, created_prize, test_pool):
        """Test update prevention for prizes used in pools"""
        # Create instance using the prize
        instance = PrizeInstance(
            pool_id=test_pool.id,
            prize_id=created_prize.id,
            individual_odds=10.0,
            status=InstanceStatus.AVAILABLE.value
        )
        db_session.add(instance)
        db_session.commit()

        # Try to update prize
        update_data = {'name': 'Updated Prize'}
        updated_prize, error = PrizeService.update_prize(
            prize_id=created_prize.id,
            data=update_data,
            admin_id=1
        )
        
        assert error is not None
        assert "Cannot update prize that is used in pools" in error

class TestPrizeValues:
    def test_prize_value_validation(self, db_session, sample_prize_data):
        """Test prize value constraints"""
        sample_prize_data['cash_value'] = Decimal('120.00')  # Higher than retail
        prize, error = PrizeService.create_prize(sample_prize_data, admin_id=1)
        
        assert error is not None
        assert 'cash_value cannot exceed retail_value' in error

    def test_credit_value_validation(self, db_session, sample_prize_data):
        """Test credit value constraints"""
        sample_prize_data['credit_value'] = Decimal('0.00')  # Invalid
        prize, error = PrizeService.create_prize(sample_prize_data, admin_id=1)
        
        assert error is not None
        assert 'credit_value must be positive' in error

class TestPrizeClaims:
    def test_claim_prize_success(self, db_session, created_prize, test_pool):
        """Test successful prize claim"""
        instance = PrizeInstance(
            pool_id=test_pool.id,
            prize_id=created_prize.id,
            individual_odds=10.0,
            status=InstanceStatus.DISCOVERED.value,
            credit_value=created_prize.credit_value
        )
        db_session.add(instance)
        db_session.commit()

        result, error = PrizeService.claim_prize(
            instance_id=instance.id,
            user_id=1,
            claim_method='credit'
        )

        assert error is None
        assert result['status'] == InstanceStatus.CLAIMED.value
        assert result['claimed_by_id'] == 1

    def test_claim_attempt_limit(self, db_session, created_prize, test_pool):
        """Test claim attempt limit enforcement"""
        instance = PrizeInstance(
            pool_id=test_pool.id,
            prize_id=created_prize.id,
            individual_odds=10.0,
            status=InstanceStatus.DISCOVERED.value,
            claim_attempts=3  # Max attempts reached
        )
        db_session.add(instance)
        db_session.commit()

        result, error = PrizeService.claim_prize(
            instance_id=instance.id,
            user_id=1
        )

        assert error is not None
        assert "Maximum claim attempts exceeded" in error

    def test_expired_claim(self, db_session, created_prize, test_pool):
        """Test handling of expired claims"""
        instance = PrizeInstance(
            pool_id=test_pool.id,
            prize_id=created_prize.id,
            individual_odds=10.0,
            status=InstanceStatus.DISCOVERED.value,
            claim_deadline=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        db_session.add(instance)
        db_session.commit()

        # Process expired claims
        count, error = PrizeService.process_expired_claims()

        assert error is None
        assert count == 1
        
        # Verify instance status
        instance = PrizeInstance.query.get(instance.id)
        assert instance.status == InstanceStatus.AVAILABLE.value
        assert instance.claim_attempts == 0

class TestPrizeRetrieval:
    def test_get_user_prizes(self, db_session, created_prize, test_pool):
        """Test getting user's claimed prizes"""
        instance = PrizeInstance(
            pool_id=test_pool.id,
            prize_id=created_prize.id,
            individual_odds=10.0,
            status=InstanceStatus.CLAIMED.value,
            claimed_by_id=1
        )
        db_session.add(instance)
        db_session.commit()

        prizes, error = PrizeService.get_user_prizes(user_id=1)

        assert error is None
        assert len(prizes) == 1
        assert prizes[0]['prize_id'] == created_prize.id
        assert prizes[0]['status'] == InstanceStatus.CLAIMED.value

    def test_get_prize_values(self, db_session, created_prize, test_pool):
        """Test getting prize value options"""
        instance = PrizeInstance(
            pool_id=test_pool.id,
            prize_id=created_prize.id,
            individual_odds=10.0,
            retail_value=created_prize.retail_value,
            cash_value=created_prize.cash_value,
            credit_value=created_prize.credit_value
        )
        db_session.add(instance)
        db_session.commit()

        values, error = PrizeService.get_prize_values(instance.id)

        assert error is None
        assert values['retail_value'] == float(created_prize.retail_value)
        assert values['cash_value'] == float(created_prize.cash_value)
        assert values['credit_value'] == float(created_prize.credit_value)