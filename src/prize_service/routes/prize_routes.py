# src/prize_service/routes/prize_routes.py

from flask import Blueprint, request, jsonify
from src.shared.auth import token_required, admin_required
from src.prize_service.services.prize_service import PrizeService
from src.prize_service.services.claim_service import ClaimService
from src.prize_service.schemas.prize_schema import (
    PrizeClaimSchema, PrizeResponseSchema, ClaimResponseSchema
)

prize_bp = Blueprint('prize', __name__, url_prefix='/api/prizes')

@prize_bp.route('/claims/<int:allocation_id>/initiate', methods=['POST'])
@token_required
def initiate_claim(allocation_id):
    """Initiate a prize claim"""
    try:
        claim_info, error = ClaimService.initiate_claim(
            allocation_id=allocation_id,
            user_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(claim_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prize_bp.route('/claims/<int:allocation_id>/process', methods=['POST'])
@token_required
def process_claim(allocation_id):
    """Process a prize claim"""
    try:
        schema = PrizeClaimSchema()
        data = schema.load(request.get_json())
        
        allocation, error = ClaimService.process_claim(
            allocation_id=allocation_id,
            user_id=request.current_user.id,
            claim_method=data['claim_method']
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(ClaimResponseSchema().dump(allocation))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prize_bp.route('/claims/<int:allocation_id>/status', methods=['GET'])
@token_required
def check_claim_status(allocation_id):
    """Check claim status"""
    try:
        status, error = ClaimService.check_claim_status(
            allocation_id=allocation_id,
            user_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prize_bp.route('/my-prizes', methods=['GET'])
@token_required
def get_my_prizes():
    """Get current user's prizes"""
    try:
        prizes, error = PrizeService.get_user_prizes(
            user_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify([PrizeResponseSchema().dump(p) for p in prizes])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500