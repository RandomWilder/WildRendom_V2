# src/prize_service/services/monitoring_service.py

from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
from src.shared import db
from src.prize_service.models import Prize, PrizePool, PrizeInstance
import logging

logger = logging.getLogger(__name__)

class PrizeMonitoringService:
    @staticmethod
    def get_pool_health(pool_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Get comprehensive pool health data"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            health_data = {
                'pool_id': pool.id,
                'status': pool.status,
                'instance_health': {
                    'total_instances': pool.total_instances,
                    'by_type': {
                        'Instant_Win': {
                            'total': 0,
                            'available': 0,
                            'discovered': 0,
                            'claimed': 0,
                            'pending_claims': 0,
                            'forfeited': 0
                        },
                        'Draw_Win': {
                            'total': 0,
                            'available': 0,
                            'allocated': 0,
                            'claimed': 0,
                            'forfeited': 0
                        }
                    }
                },
                'value_tracking': {
                    'total_pool_value': {
                        'retail': float(pool.retail_total or 0),
                        'cash': float(pool.cash_total or 0),
                        'credit': float(pool.credit_total or 0)
                    },
                    'claimed_value': {
                        'retail': 0,
                        'cash': 0,
                        'credit': 0
                    }
                },
                'claim_metrics': {
                    'average_claim_time': "00:00:00",
                    'claims_expiring_soon': 0,
                    'expired_claims_24h': 0
                }
            }

            # Calculate instance health
            instances = PrizeInstance.query.filter_by(pool_id=pool_id).all()
            for instance in instances:
                prize = db.session.get(Prize, instance.prize_id)
                if not prize:
                    continue

                type_stats = health_data['instance_health']['by_type'][prize.type]
                type_stats['total'] += 1

                if instance.status == 'available':
                    type_stats['available'] += 1
                elif instance.status == 'discovered':
                    type_stats['discovered'] += 1
                    type_stats['pending_claims'] += 1
                elif instance.status == 'claimed':
                    type_stats['claimed'] += 1
                    for value_type in ['retail', 'cash', 'credit']:
                        value = getattr(instance, f"{value_type}_value")
                        health_data['value_tracking']['claimed_value'][value_type] += float(value)

            # Calculate claim metrics
            current_time = datetime.now(timezone.utc)
            claimed_instances = [i for i in instances if i.status == 'claimed' and i.claimed_at]
            if claimed_instances:
                total_claim_time = sum((i.claimed_at - i.created_at).total_seconds() for i in claimed_instances)
                avg_claim_time = total_claim_time / len(claimed_instances)
                hours = int(avg_claim_time // 3600)
                minutes = int((avg_claim_time % 3600) // 60)
                seconds = int(avg_claim_time % 60)
                health_data['claim_metrics']['average_claim_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Count expiring claims
            health_data['claim_metrics']['claims_expiring_soon'] = PrizeInstance.query.filter(
                and_(
                    PrizeInstance.pool_id == pool_id,
                    PrizeInstance.status == 'discovered',
                    PrizeInstance.claim_deadline <= current_time + timedelta(hours=1)
                )
            ).count()

            # Count recently expired claims
            health_data['claim_metrics']['expired_claims_24h'] = PrizeInstance.query.filter(
                and_(
                    PrizeInstance.pool_id == pool_id,
                    PrizeInstance.status == 'available',
                    PrizeInstance.updated_at >= current_time - timedelta(hours=24),
                    PrizeInstance.claim_attempts > 0
                )
            ).count()

            return health_data, None

        except Exception as e:
            logger.error(f"Error getting pool health: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_pool_audit(pool_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """Get audit trail for pool"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            # Parse dates if provided
            try:
                if start_date:
                    start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if end_date:
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return None, "Invalid date format"

            # Base query for instances
            query = PrizeInstance.query.filter_by(pool_id=pool_id)
            if start_date:
                query = query.filter(PrizeInstance.created_at >= start_date)
            if end_date:
                query = query.filter(PrizeInstance.created_at <= end_date)

            instances = query.all()

            audit_data = {
                'pool_id': pool_id,
                'creation': {
                    'timestamp': pool.created_at.isoformat(),
                    'admin_id': pool.created_by_id
                },
                'instance_allocation_history': [],
                'status_changes': [],
                'instance_activity': []
            }

            # Collect instance allocations
            for instance in instances:
                allocation_record = {
                    'timestamp': instance.created_at.isoformat(),
                    'instance_id': instance.instance_id,
                    'prize_id': instance.prize_id,
                    'status': instance.status
                }
                audit_data['instance_allocation_history'].append(allocation_record)

                # Add claim activity if exists
                if instance.claimed_at:
                    claim_record = {
                        'instance_id': instance.instance_id,
                        'timestamp': instance.claimed_at.isoformat(),
                        'claimed_by': instance.claimed_by_id,
                        'value_claimed': float(instance.credit_value)
                    }
                    audit_data['instance_activity'].append(claim_record)

            return audit_data, None

        except Exception as e:
            logger.error(f"Error getting pool audit: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_pool_alerts(pool_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Get active alerts for pool"""
        try:
            pool = db.session.get(PrizePool, pool_id)
            if not pool:
                return None, "Pool not found"

            current_time = datetime.now(timezone.utc)
            alerts = []

            # Check expiring claims
            expiring_claims = PrizeInstance.query.filter(
                and_(
                    PrizeInstance.pool_id == pool_id,
                    PrizeInstance.status == 'discovered',
                    PrizeInstance.claim_deadline <= current_time + timedelta(hours=1)
                )
            ).count()

            if expiring_claims > 0:
                alerts.append({
                    'type': 'expiring_claims',
                    'severity': 'warning',
                    'message': f'{expiring_claims} claims expiring within 1 hour',
                    'timestamp': current_time.isoformat()
                })

            # Check high forfeiture rate
            recent_claims = PrizeInstance.query.filter(
                and_(
                    PrizeInstance.pool_id == pool_id,
                    PrizeInstance.updated_at >= current_time - timedelta(hours=1)
                )
            ).count()

            recent_forfeitures = PrizeInstance.query.filter(
                and_(
                    PrizeInstance.pool_id == pool_id,
                    PrizeInstance.updated_at >= current_time - timedelta(hours=1),
                    PrizeInstance.status == 'available',
                    PrizeInstance.claim_attempts > 0
                )
            ).count()

            if recent_claims > 0:
                forfeiture_rate = (recent_forfeitures / recent_claims) * 100
                if forfeiture_rate > 20:  # Alert if >20% forfeiture rate
                    alerts.append({
                        'type': 'high_forfeiture_rate',
                        'severity': 'warning',
                        'message': f'High forfeiture rate: {forfeiture_rate:.1f}% in last hour',
                        'timestamp': current_time.isoformat()
                    })

            # Check pool depletion
            if pool.available_instances < (pool.total_instances * 0.1):  # Less than 10% remaining
                alerts.append({
                    'type': 'low_instances',
                    'severity': 'warning',
                    'message': f'Low available instances: {pool.available_instances} remaining',
                    'timestamp': current_time.isoformat()
                })

            return {'alerts': alerts}, None

        except Exception as e:
            logger.error(f"Error getting pool alerts: {str(e)}")
            return None, str(e)