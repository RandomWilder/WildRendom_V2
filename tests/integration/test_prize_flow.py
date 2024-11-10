# tests/integration/test_prize_flow.py

import pytest
from datetime import datetime, timezone, timedelta
from src.prize_service.services.prize_service import PrizeService
from src.prize_service.services.credit_service import CreditService
from src.raffle_service.services.instant_win_service import InstantWinService
from src.prize_service.models import Prize, PrizePool, PrizeAllocation, ClaimStatus
from src.raffle_service.models import InstantWin, InstantWinStatus, Ticket, TicketStatus
from src.user_service.models import User, CreditTransaction
from src.shared import db

@pytest.fixture
def setup_raffle_and_pool(db_session):
    """Create test raffle with prize pool"""
    # Create prize pool
    pool = PrizePool(
        name="Test Pool",
        status="locked",
        allocation_strategy="odds_based",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=7),
        odds_configuration={
            'prizes': [{'prize_id': 1, 'odds': 100}]  # Single prize for predictable testing
        },
        total_prizes=10,
        available_prizes=10,
        created_by_id=1
    )
    
    # Create prize
    prize = Prize(
        id=1,
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
    
    db_session.add(pool)
    db_session.add(prize)
    db_session.commit()
    
    return {"pool": pool, "prize": prize}

@pytest.fixture
def setup_test_user(db_session):
    """Create test user with initial credits"""
    user = User(
        username="testuser",
        email="test@example.com",
        site_credits=500.0,
        is_active=True
    )
    user.set_password("test123")
    db_session.add(user)
    db_session.commit()
    return user

class TestPrizeIntegration:
    def test_complete_instant_win_flow(self, db_session, setup_raffle_and_pool, setup_test_user):
        """Test complete flow: Instant Win -> Prize Allocation -> Claim -> Credit Award"""
        pool = setup_raffle_and_pool["pool"]
        user = setup_test_user
        initial_credits = user.site_credits

        # Step 1: Create test ticket
        ticket = Ticket(
            raffle_id=1,  # Test raffle ID
            ticket_number="001",
            status=TicketStatus.SOLD.value,
            user_id=user.id,
            instant_win=True,
            instant_win_eligible=True
        )
        db_session.add(ticket)
        db_session.commit()

        # Step 2: Create and discover instant win
        instant_win = InstantWin(
            raffle_id=1,
            ticket_id=ticket.id,
            status=InstantWinStatus.ALLOCATED.value
        )
        db_session.add(instant_win)
        db_session.commit()

        # Step 3: Check instant win and get prize allocation
        instant_win, error = InstantWinService.check_instant_win(ticket.id)
        assert error is None
        assert instant_win is not None
        assert instant_win.status == InstantWinStatus.DISCOVERED.value

        # Get the prize allocation from the reference
        allocation = PrizeAllocation.query.get(int(instant_win.prize_reference))
        assert allocation is not None
        assert allocation.claim_status == ClaimStatus.PENDING.value

        # Step 4: Claim the prize
        result, error = PrizeService.claim_prize(
            allocation_id=allocation.id,
            user_id=user.id,
            claim_method='credit'
        )
        assert error is None
        assert result is not None
        assert result.claim_status == ClaimStatus.CLAIMED.value

        # Step 5: Verify credit award
        db_session.refresh(user)
        assert user.site_credits == initial_credits + allocation.original_value

        # Step 6: Verify credit transaction
        transaction = CreditTransaction.query.filter_by(
            user_id=user.id,
            reference_type='prize_claim',
            reference_id=str(allocation.id)
        ).first()
        assert transaction is not None
        assert transaction.amount == allocation.original_value

    def test_expired_claim_flow(self, db_session, setup_raffle_and_pool, setup_test_user):
        """Test flow with expired claim"""
        pool = setup_raffle_and_pool["pool"]
        user = setup_test_user
        initial_credits = user.site_credits

        # Create expired allocation
        allocation, _ = PrizeService.allocate_instant_win(
            pool_id=pool.id,
            ticket_id="TEST-EXP",
            user_id=user.id
        )
        
        # Expire it
        allocation.claim_deadline = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.commit()

        # Try to claim
        result, error = PrizeService.claim_prize(
            allocation_id=allocation.id,
            user_id=user.id,
            claim_method='credit'
        )

        # Verify claim rejected
        assert error == "Prize claim has expired"
        assert result is None

        # Verify no credits awarded
        db_session.refresh(user)
        assert user.site_credits == initial_credits

        # Verify no transaction created
        transaction = CreditTransaction.query.filter_by(
            user_id=user.id,
            reference_type='prize_claim',
            reference_id=str(allocation.id)
        ).first()
        assert transaction is None

    def test_concurrent_claim_handling(self, db_session, setup_raffle_and_pool, setup_test_user):
        """Test handling of concurrent claims"""
        pool = setup_raffle_and_pool["pool"]
        user = setup_test_user

        # Create allocation
        allocation, _ = PrizeService.allocate_instant_win(
            pool_id=pool.id,
            ticket_id="TEST-CONCURRENT",
            user_id=user.id
        )

        # First claim should succeed
        result1, error1 = PrizeService.claim_prize(
            allocation_id=allocation.id,
            user_id=user.id,
            claim_method='credit'
        )
        assert error1 is None
        assert result1 is not None

        # Second claim should fail
        result2, error2 = PrizeService.claim_prize(
            allocation_id=allocation.id,
            user_id=user.id,
            claim_method='credit'
        )
        assert error2 is not None
        assert "Prize cannot be claimed" in error2
        