# src/prize_service/routes/admin_routes.py

import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text
from src.shared.auth import admin_required
from src.shared import db
from src.prize_service.services.admin_monitoring_service import PrizeAdminMonitoringService
from src.prize_service.services.monitoring_service import PrizeMonitoringService
from src.prize_service.services.prize_service import PrizeService
from src.prize_service.services.claim_service import ClaimService
from src.prize_service.services.monitoring_service import PrizeMonitoringService
from src.prize_service.models import (
    Prize, PrizePool, PrizeAllocation,
    PrizeStatus, PoolStatus, ClaimStatus,
    AllocationType
)
from src.prize_service.schemas.prize_schema import (
    PrizeCreateSchema, 
    PrizeUpdateSchema,
    PrizePoolCreateSchema,
    PrizeAllocationCreateSchema,
    PrizeResponseSchema
)

admin_bp = Blueprint('prize_admin', __name__)
logger = logging.getLogger(__name__)

# Prize Template Management Endpoints

@admin_bp.route('/create', methods=['POST'])
@admin_required
def create_prize():
    """Create a new prize template"""
    try:
        schema = PrizeCreateSchema()
        data = schema.load(request.get_json())
        
        prize, error = PrizeService.create_prize(
            data=data,
            admin_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(prize.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating prize: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/prizes', methods=['GET'])
@admin_required
def list_prizes():
    """Get all prize templates"""
    try:
        prizes = Prize.query.all()
        return jsonify({
            'templates': [prize.to_dict() for prize in prizes]
        })
    except Exception as e:
        logger.error(f"Error listing prizes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/prizes/<int:prize_id>', methods=['GET'])
@admin_required
def get_prize(prize_id):
    """Get prize template details"""
    try:
        prize = Prize.query.get(prize_id)
        if not prize:
            return jsonify({'error': 'Prize not found'}), 404
            
        return jsonify(prize.to_dict())
    except Exception as e:
        logger.error(f"Error getting prize: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/prizes/<int:prize_id>', methods=['PUT'])
@admin_required
def update_prize(prize_id):
    """Update prize template if not used in any pool"""
    try:
        prize = Prize.query.get(prize_id)
        if not prize:
            return jsonify({'error': 'Prize not found'}), 404

        # Check if prize is used in any pool
        if PrizeAllocation.query.filter_by(prize_id=prize_id).first():
            return jsonify({'error': 'Cannot update prize that is used in pools'}), 400

        schema = PrizeUpdateSchema()
        data = schema.load(request.get_json())
        
        updated_prize, error = PrizeService.update_prize(
            prize_id=prize_id,
            data=data,
            admin_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(updated_prize.to_dict())
    except Exception as e:
        logger.error(f"Error updating prize: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Prize Pool Management Endpoints

@admin_bp.route('/pools', methods=['POST'])
@admin_required
def create_pool():
    """Create a new empty prize pool"""
    try:
        schema = PrizePoolCreateSchema()
        data = schema.load(request.get_json())
        
        pool, error = PrizeService.create_pool(
            data=data,
            admin_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        # Return the response directly since it's already formatted
        return jsonify(pool), 201
    except Exception as e:
        logger.error(f"Error creating prize pool: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/prizes/pools/<int:pool_id>/allocate', methods=['POST'])
@admin_required
def allocate_pool_prizes(pool_id):
    """Allocate prizes to pool with odds configuration"""
    try:
        schema = PrizeAllocationCreateSchema()
        data = schema.load(request.get_json())
        
        if 'prize_template_id' not in data or 'instance_count' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        allocation, error = PrizeService.allocate_to_pool(
            pool_id=pool_id,
            prize_id=data['prize_template_id'],
            quantity=data['instance_count'],
            collective_odds=data.get('collective_odds', 0),
            admin_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(allocation), 201
    except Exception as e:
        logger.error(f"Error allocating prizes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/prizes/pools/<int:pool_id>', methods=['GET'])
@admin_required
def get_pool(pool_id):
    """Get prize pool details"""
    try:
        pool = PrizePool.query.get(pool_id)
        if not pool:
            return jsonify({'error': 'Prize pool not found'}), 404
            
        return jsonify(pool.to_dict())
    except Exception as e:
        logger.error(f"Error getting pool: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/prizes/pools/<int:pool_id>/claim-stats', methods=['GET'])
@admin_required
def get_pool_claim_stats(pool_id):
    """Get claim statistics for a pool"""
    try:
        stats, error = PrizeService.get_pool_claim_stats(pool_id)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting claim stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/prizes/pools/<int:pool_id>/lock', methods=['PUT'])
@admin_required
def lock_pool(pool_id):
    """Lock prize pool with validation"""
    try:
        pool = PrizePool.query.get(pool_id)
        if not pool:
            return jsonify({'error': 'Prize pool not found'}), 404

        result, error = PrizeService.lock_pool(
            pool_id=pool_id,
            admin_id=request.current_user.id
        )
        
        if error:
            return jsonify({
                'success': False,
                'error': error,
                'status': pool.status
            }), 400
            
        return jsonify({
            'success': True,
            'status': 'locked',
            'validation': result
        })
    except Exception as e:
        logger.error(f"Error locking pool: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Basic Monitoring Endpoints (To be migrated to analysis service later)

@admin_bp.route('/prizes/monitoring/pools/<int:pool_id>/health', methods=['GET'])
@admin_required
def get_pool_health(pool_id):
    """Get pool health metrics"""
    try:
        health_data, error = PrizeMonitoringService.get_pool_health(pool_id)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(health_data)
    except Exception as e:
        logger.error(f"Error getting pool health: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@admin_bp.route('/monitoring/system', methods=['GET'])
@admin_required
def get_system_metrics():
    """Get system-wide monitoring stats"""
    try:
        metrics, error = PrizeAdminMonitoringService.get_system_metrics()
        if error:
            return jsonify({'error': error}), 400
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/monitoring/pools/<int:pool_id>/health', methods=['GET'])
@admin_required
def get_pool_monitoring_health(pool_id):  # Changed function name here
    """Get pool health monitoring data"""
    try:
        health_data, error = PrizeMonitoringService.get_pool_health(pool_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(health_data)
    except Exception as e:
        logger.error(f"Error getting pool health: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/monitoring/performance', methods=['GET'])
@admin_required
def get_performance_metrics():
    """Get system performance metrics"""
    try:
        metrics, error = PrizeAdminMonitoringService.get_performance_metrics()
        if error:
            return jsonify({'error': error}), 400
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500