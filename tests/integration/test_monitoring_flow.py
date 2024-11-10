# tests/integration/test_monitoring_flow.py

import pytest
from datetime import datetime, timezone, timedelta
from src.prize_service.services.monitoring_service import PrizeMonitoringService
from src.prize_service.services.admin_monitoring_service import PrizeAdminMonitoringService
from src.prize_service.models import (
    Prize, PrizePool, PrizeInstance,
    PoolStatus, ClaimStatus, AllocationType, InstanceStatus
)
from src.shared import db
import threading
import time
from flask import current_app

class TestMonitoringIntegration:
    def test_pool_health_monitoring(self, db_session, test_pool, test_prizes, app):
        """Test complete pool health monitoring flow"""
        with app.app_context():
            # Set up test data
            pool = test_pool
            prize = test_prizes[0]
            
            # Create some prize instances
            for _ in range(5):
                instance = PrizeInstance(
                    pool_id=pool.id,
                    prize_id=prize.id,
                    status=InstanceStatus.AVAILABLE.value,
                    individual_odds=20.0,
                    created_by_id=1,
                    claim_deadline=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                db_session.add(instance)
            db_session.commit()

            # Test health monitoring
            health_data, error = PrizeMonitoringService.get_pool_health(pool.id)
            
            assert error is None
            assert health_data is not None
            assert health_data['instance_health']['total_instances'] == 5
            assert health_data['value_tracking']['total_pool_value']['credit'] > 0

    def test_performance_under_load(self, db_session, test_pool, test_prizes, app):
        """Test monitoring performance under concurrent operations"""
        def concurrent_operation(pool_id):
            with app.app_context():
                health_data, _ = PrizeMonitoringService.get_pool_health(pool_id)
                return health_data is not None

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(
                target=concurrent_operation,
                args=(test_pool.id,)
            )
            threads.append(thread)

        start_time = time.time()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert time.time() - start_time < 2.0

    def test_system_metrics_accuracy(self, db_session, test_pool, test_prizes, app):
        """Test accuracy of system-wide metrics"""
        with app.app_context():
            # Create test instances
            for _ in range(3):
                instance = PrizeInstance(
                    pool_id=test_pool.id,
                    prize_id=test_prizes[0].id,
                    status=InstanceStatus.CLAIMED.value,
                    claimed_at=datetime.now(timezone.utc),
                    individual_odds=10.0,
                    created_by_id=1,
                    claim_deadline=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                db_session.add(instance)
            db_session.commit()

            metrics, error = PrizeAdminMonitoringService.get_system_metrics()
            
            assert error is None
            assert 'instant_wins_24h' in metrics
            assert metrics['system_health']['claim_success_rate'] > 0

    def test_edge_cases(self, db_session, test_pool, test_prizes, app):
        """Test monitoring edge cases"""
        with app.app_context():
            # Test empty pool
            health_data, error = PrizeMonitoringService.get_pool_health(test_pool.id)
            assert error is None
            assert health_data['instance_health']['total_instances'] == 0

            # Test expired claims
            instance = PrizeInstance(
                pool_id=test_pool.id,
                prize_id=test_prizes[0].id,
                status=InstanceStatus.AVAILABLE.value,
                individual_odds=10.0,
                claim_deadline=datetime.now(timezone.utc) - timedelta(hours=1),
                created_by_id=1
            )
            db_session.add(instance)
            db_session.commit()

            health_data, _ = PrizeMonitoringService.get_pool_health(test_pool.id)
            assert health_data['claim_metrics']['expired_claims_24h'] >= 0

class TestPerformanceMonitoring:
    def test_high_volume_operations(self, db_session, test_pool, test_prizes, app):
        """Test monitoring under high volume operations"""
        def perform_check():
            with app.app_context():
                return PrizeMonitoringService.get_pool_health(test_pool.id)

        start_time = time.time()
        operations = []
        
        for _ in range(50):
            thread = threading.Thread(target=perform_check)
            operations.append(thread)
            thread.start()

        for op in operations:
            op.join()

        assert time.time() - start_time < 5.0

    def test_data_consistency(self, db_session, test_pool, test_prizes, app):
        """Test monitoring data consistency under concurrent updates"""
        def update_operation(pool_id, prize_id):
            with app.app_context():
                instance = PrizeInstance(
                    pool_id=pool_id,
                    prize_id=prize_id,
                    status=InstanceStatus.AVAILABLE.value,
                    individual_odds=10.0,
                    created_by_id=1,
                    claim_deadline=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                db_session.add(instance)
                instance.status = InstanceStatus.CLAIMED.value
                instance.claimed_at = datetime.now(timezone.utc)
                db_session.commit()

        threads = [
            threading.Thread(
                target=update_operation,
                args=(test_pool.id, test_prizes[0].id)
            )
            for _ in range(10)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        with app.app_context():
            health_data, _ = PrizeMonitoringService.get_pool_health(test_pool.id)
            metrics, _ = PrizeAdminMonitoringService.get_system_metrics()

            assert health_data['instance_health']['total_instances'] >= 10
            assert metrics is not None