# tests/prize_service/test_credit_service.py

import pytest
from datetime import datetime, timezone, timedelta
from src.prize_service.services.credit_service import CreditService
from src.prize_service.models import PrizeAllocation, ClaimStatus
from src.user_service.models import User, CreditTransaction
from src.prize_service.models import Prize, PrizePool

@pytest.fixture
def setup_test_allocation(db_session, test_user):
    """Create test allocation for credit processing"""
    # Create a test prize first
    prize = Prize(
        name="Test Prize",
        type="instant_win",
        tier="silver",
        retail_value=100.0,
        cash_value=100.0,
        credit_value=100.0,
        total_quantity=10,
        available_quantity=10,
        status="active",
        created_by_id=1
    )
    
    pool = PrizePool(
        name="Test Pool",
        status="locked",
        allocation_strategy="odds_based",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=7),
        created_by_id=1
    )
    
    db_session.add(prize)
    db_session.add(pool)
    db_session.flush()
    
    allocation = PrizeAllocation(
        prize_id=prize.id,
        pool_id=pool.id,
        allocation_type='instant_win',
        reference_type='test',
        reference_id='TEST-001',
        winner_user_id=test_user.id,
        claim_status=ClaimStatus.PENDING.value,
        original_value=100.0,
        claim_deadline=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db_session.add(allocation)
    db_session.commit()
    return allocation

class TestCreditService:
    def test_process_prize_claim(self, db_session, test_user, setup_test_allocation):
        """Test credit processing for prize claim"""
        initial_credits = test_user.site_credits
        allocation = setup_test_allocation

        # Process claim
        result, error = CreditService.process_prize_claim(
            allocation_id=allocation.id,
            user_id=test_user.id
        )

        assert error is None
        assert result is not None
        assert 'transaction_id' in result
        assert 'amount_awarded' in result
        assert result['amount_awarded'] == allocation.original_value

        # Verify user credits updated
        db_session.refresh(test_user)
        assert test_user.site_credits == initial_credits + allocation.original_value

        # Verify transaction created
        transaction = db_session.query(CreditTransaction)\
            .filter_by(id=result['transaction_id'])\
            .first()
        assert transaction is not None
        assert transaction.amount == allocation.original_value
        assert transaction.transaction_type == 'add'
        assert transaction.reference_type == 'prize_claim'

    def test_verify_claim_eligibility(self, db_session, test_user, setup_test_allocation):
        """Test claim eligibility verification"""
        allocation = setup_test_allocation
        
        # Test valid claim
        eligible, error = CreditService.verify_claim_eligibility(
            allocation_id=allocation.id,
            user_id=test_user.id
        )
        assert eligible is True
        assert error is None

        # Test expired claim
        allocation.claim_deadline = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.commit()

        eligible, error = CreditService.verify_claim_eligibility(
            allocation_id=allocation.id,
            user_id=test_user.id
        )
        assert eligible is False
        assert "Claim deadline has passed" in error

    def test_process_claim_with_insufficient_pool_budget(self, db_session, test_user, setup_test_allocation):
        """Test claim processing when pool budget is exceeded"""
        allocation = setup_test_allocation
        
        # Set pool budget limit
        pool = db_session.query(PrizePool).get(allocation.pool_id)
        pool.budget_limit = 50.0  # Less than prize value
        db_session.commit()

        result, error = CreditService.process_prize_claim(
            allocation_id=allocation.id,
            user_id=test_user.id
        )

        assert error is not None
        assert "Pool budget exceeded" in error
        
        # Verify no credits awarded
        db_session.refresh(test_user)
        assert test_user.site_credits == test_user.site_credits

    def test_concurrent_claims(self, db_session, test_user, setup_test_allocation):
        """Test handling of concurrent claim attempts"""
        allocation = setup_test_allocation
        initial_credits = test_user.site_credits

        # First claim should succeed
        result1, error1 = CreditService.process_prize_claim(
            allocation_id=allocation.id,
            user_id=test_user.id
        )
        assert error1 is None
        assert result1 is not None

        # Second claim should fail
        result2, error2 = CreditService.process_prize_claim(
            allocation_id=allocation.id,
            user_id=test_user.id
        )
        assert error2 is not None
        assert "already claimed" in error2

        # Verify only one credit transaction occurred
        transactions = db_session.query(CreditTransaction)\
            .filter_by(
                user_id=test_user.id,
                reference_type='prize_claim',
                reference_id=str(allocation.id)
            ).all()
        assert len(transactions) == 1