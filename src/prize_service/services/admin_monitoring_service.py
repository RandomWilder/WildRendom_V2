# src/prize_service/services/admin_monitoring_service.py

from typing import Optional, Tuple, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func
from src.shared import db
from src.prize_service.models import Prize, PrizePool, PrizeInstance
import logging

logger = logging.getLogger(__name__)

class PrizeAdminMonitoringService:
    @staticmethod
    def get_system_metrics() -> Tuple[Optional[Dict], Optional[str]]:
        """Get system-wide monitoring metrics"""
        try:
            current_time = datetime.now(timezone.utc)
            one_day_ago = current_time - timedelta(days=1)

            metrics = {
                'active_pools': {
                    'total': PrizePool.query.filter(
                        PrizePool.status.in_(['unlocked', 'locked'])
                    ).count(),
                    'by_status': {
                        'unlocked': PrizePool.query.filter_by(status='unlocked').count(),
                        'locked': PrizePool.query.filter_by(status='locked').count(),
                        'used': PrizePool.query.filter_by(status='used').count()
                    }
                },
                'instant_wins_24h': {
                    'discoveries': PrizeInstance.query.filter(
                        and_(
                            PrizeInstance.status == 'discovered',
                            PrizeInstance.updated_at >= one_day_ago
                        )
                    ).count(),
                    'claims': PrizeInstance.query.filter(
                        and_(
                            PrizeInstance.status == 'claimed',
                            PrizeInstance.claimed_at >= one_day_ago
                        )
                    ).count(),
                    'forfeitures': PrizeInstance.query.filter(
                        and_(
                            PrizeInstance.status == 'available',
                            PrizeInstance.claim_attempts > 0,
                            PrizeInstance.updated_at >= one_day_ago
                        )
                    ).count()
                },
                'system_health': {
                    'pools_needing_attention': [],
                    'total_active_instances': PrizeInstance.query.filter(
                        PrizeInstance.status.in_(['available', 'discovered'])
                    ).count(),
                    'claim_success_rate': 0.0
                }
            }

            # Calculate average claim time
            claimed_instances = PrizeInstance.query.filter(
                and_(
                    PrizeInstance.status == 'claimed',
                    PrizeInstance.claimed_at >= one_day_ago
                )
            ).all()

            if claimed_instances:
                total_claim_time = sum(
                    (inst.claimed_at - inst.created_at).total_seconds()
                    for inst in claimed_instances
                )
                avg_claim_time = total_claim_time / len(claimed_instances)
                metrics['instant_wins_24h']['average_claim_time'] = f"{int(avg_claim_time // 3600):02d}:{int((avg_claim_time % 3600) // 60):02d}:{int(avg_claim_time % 60):02d}"
            else:
                metrics['instant_wins_24h']['average_claim_time'] = "00:00:00"

            # Calculate claim success rate
            total_attempts = metrics['instant_wins_24h']['claims'] + metrics['instant_wins_24h']['forfeitures']
            if total_attempts > 0:
                metrics['system_health']['claim_success_rate'] = (
                    metrics['instant_wins_24h']['claims'] / total_attempts
                ) * 100

            # Identify pools needing attention
            active_pools = PrizePool.query.filter(
                PrizePool.status.in_(['unlocked', 'locked'])
            ).all()

            for pool in active_pools:
                issues = []
                
                # Check for high forfeiture rate
                pool_forfeitures = PrizeInstance.query.filter(
                    and_(
                        PrizeInstance.pool_id == pool.id,
                        PrizeInstance.status == 'available',
                        PrizeInstance.claim_attempts > 0,
                        PrizeInstance.updated_at >= one_day_ago
                    )
                ).count()
                
                pool_claims = PrizeInstance.query.filter(
                    and_(
                        PrizeInstance.pool_id == pool.id,
                        PrizeInstance.status == 'claimed',
                        PrizeInstance.claimed_at >= one_day_ago
                    )
                ).count()

                if pool_claims + pool_forfeitures > 0:
                    forfeiture_rate = (pool_forfeitures / (pool_claims + pool_forfeitures)) * 100
                    if forfeiture_rate > 20:  # Alert if >20% forfeiture rate
                        issues.append({
                            'issue': 'high_forfeiture_rate',
                            'details': f"{forfeiture_rate:.1f}% forfeiture in last 24h"
                        })

                # Check for low available instances
                if pool.available_instances < (pool.total_instances * 0.1):  # Less than 10% remaining
                    issues.append({
                        'issue': 'low_instances',
                        'details': f"Only {pool.available_instances} instances remaining"
                    })

                if issues:
                    metrics['system_health']['pools_needing_attention'].append({
                        'pool_id': pool.id,
                        'pool_name': pool.name,
                        'issues': issues
                    })

            return metrics, None

        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_performance_metrics() -> Tuple[Optional[Dict], Optional[str]]:
        """Get detailed performance metrics"""
        try:
            current_time = datetime.now(timezone.utc)
            one_day_ago = current_time - timedelta(days=1)
            
            metrics = {
                'time_period': 'last_24h',
                'ticket_operations': {
                    'reveals': {
                        'total_count': 0,
                        'average_response_time': "00:00:00.000",
                        'instant_wins_discovered': 0
                    }
                },
                'claim_operations': {
                    'instant_wins': {
                        'total_claims': 0,
                        'average_processing_time': "00:00:00.000",
                        'success_rate': 0.0
                    },
                    'draw_wins': {
                        'total_claims': 0,
                        'average_processing_time': "00:00:00.000",
                        'success_rate': 0.0
                    }
                },
                'system_load': {
                    'peak_concurrent_users': 0,
                    'peak_transactions_per_minute': 0,
                    'average_response_time': "00:00:00.000"
                }
            }

            # Calculate instant win metrics
            instant_wins = PrizeInstance.query.filter(
                and_(
                    PrizeInstance.status.in_(['claimed', 'available']),
                    PrizeInstance.updated_at >= one_day_ago
                )
            ).all()

            if instant_wins:
                successful_claims = [w for w in instant_wins if w.status == 'claimed']
                metrics['claim_operations']['instant_wins'].update({
                    'total_claims': len(instant_wins),
                    'success_rate': (len(successful_claims) / len(instant_wins)) * 100 if instant_wins else 0.0
                })

                if successful_claims:
                    total_processing_time = sum(
                        (w.claimed_at - w.created_at).total_seconds()
                        for w in successful_claims if w.claimed_at
                    )
                    avg_time = total_processing_time / len(successful_claims)
                    metrics['claim_operations']['instant_wins']['average_processing_time'] = f"00:00:{avg_time:.3f}"

            return metrics, None

        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_pool_distribution_metrics(pool_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Get prize distribution metrics for a pool"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            distribution_metrics = {
                'pool_id': pool_id,
                'total_prizes': pool.total_instances,
                'prize_types': {
                    'instant_win': {
                        'count': pool.instant_win_count,
                        'distributed': 0,
                        'value_distributed': 0.0
                    },
                    'draw_win': {
                        'count': pool.draw_win_count,
                        'distributed': 0,
                        'value_distributed': 0.0
                    }
                },
                'distribution_timeline': []
            }

            # Calculate distribution by type
            for prize_type in ['instant_win', 'draw_win']:
                claimed_instances = PrizeInstance.query.join(Prize).filter(
                    PrizeInstance.pool_id == pool_id,
                    PrizeInstance.status == 'claimed',
                    func.lower(Prize.type) == prize_type
                ).all()

                distribution_metrics['prize_types'][prize_type].update({
                    'distributed': len(claimed_instances),
                    'value_distributed': sum(float(inst.credit_value) for inst in claimed_instances)
                })

            # Get hourly distribution for last 24 hours
            current_time = datetime.now(timezone.utc)
            for hour in range(24):
                hour_start = current_time - timedelta(hours=hour+1)
                hour_end = current_time - timedelta(hours=hour)
                
                hour_claims = PrizeInstance.query.filter(
                    PrizeInstance.pool_id == pool_id,
                    PrizeInstance.status == 'claimed',
                    PrizeInstance.claimed_at.between(hour_start, hour_end)
                ).count()

                distribution_metrics['distribution_timeline'].append({
                    'hour': hour,
                    'claims': hour_claims,
                    'timestamp': hour_start.isoformat()
                })

            return distribution_metrics, None

        except Exception as e:
            logger.error(f"Error getting distribution metrics: {str(e)}")
            return None, str(e)