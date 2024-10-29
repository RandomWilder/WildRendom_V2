# src/prize_service/routes/admin_routes.py

from flask import Blueprint, request, jsonify
from src.shared.auth import admin_required
from src.prize_service.services.prize_service import PrizeService
from src.prize_service.services.claim_service import ClaimService
from src.prize_service.models import Prize, PrizePool, PrizePoolAllocation
from src.prize_service.schemas.prize_schema import (
    PrizeCreateSchema, PrizePoolCreateSchema,
    PrizeAllocationCreateSchema
)

admin_bp = Blueprint('prize_admin', __name__, url_prefix='/api/admin/prizes')

@admin_bp.route('/create', methods=['POST'])
@admin_required
def create_prize():
    """Create a new prize"""
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
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/pools', methods=['POST'])
@admin_required
def create_pool():
    """Create a new prize pool"""
    try:
        schema = PrizePoolCreateSchema()
        data = schema.load(request.get_json())
        
        pool, error = PrizeService.create_pool(
            data=data,
            admin_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(pool.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/pools/<int:pool_id>/allocations', methods=['POST'])
@admin_required
def create_pool_allocation(pool_id: int):  # Added pool_id parameter
    """Add prizes to a pool"""
    try:
        schema = PrizeAllocationCreateSchema()
        data = schema.load(request.get_json())
        
        allocation, error = PrizeService.create_pool_allocation(
            pool_id=pool_id,
            data=data,
            admin_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(allocation.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/claims/expire', methods=['POST'])
@admin_required
def expire_stale_claims():
    """Expire stale claims"""
    try:
        count, error = ClaimService.expire_stale_claims()
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify({
            'expired_count': count,
            'message': f'Successfully expired {count} stale claims'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@admin_bp.route('/pools/<int:pool_id>', methods=['GET'])
@admin_required
def get_pool(pool_id):
    """Get prize pool details"""
    try:
        pool = PrizePool.query.get(pool_id)
        if not pool:
            return jsonify({'error': 'Prize pool not found'}), 404
            
        return jsonify(pool.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/pools/<int:pool_id>/allocations', methods=['GET'])
@admin_required
def get_pool_allocations(pool_id):
    """Get all allocations for a pool"""
    try:
        allocations = PrizePoolAllocation.query.filter_by(pool_id=pool_id).all()
        if not allocations:
            return jsonify([])
            
        return jsonify([alloc.to_dict() for alloc in allocations])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/prizes/<int:prize_id>', methods=['GET'])
@admin_required
def get_prize(prize_id):
    """Get prize details"""
    try:
        prize = Prize.query.get(prize_id)
        if not prize:
            return jsonify({'error': 'Prize not found'}), 404
            
        return jsonify(prize.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/pools', methods=['GET'])
@admin_required
def get_all_pools():
    """Get all prize pools"""
    try:
        pools = PrizePool.query.all()
        return jsonify([pool.to_dict() for pool in pools])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500