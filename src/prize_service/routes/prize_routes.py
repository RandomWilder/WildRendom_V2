# src/prize_service/routes/prize_routes.py

from flask import Blueprint, request, jsonify
from src.shared.auth import token_required, admin_required
from src.prize_service.services.prize_service import PrizeService
from src.prize_service.services.claim_service import ClaimService
from src.raffle_service.models import InstantWin
from src.prize_service.models import Prize, PrizePool, PrizeAllocation
from src.prize_service.schemas.prize_schema import (
    PrizeClaimSchema, PrizeResponseSchema, ClaimResponseSchema
)

prize_bp = Blueprint('prize', __name__, url_prefix='/api/prizes')

@prize_bp.route('/claims/<int:allocation_id>/initiate', methods=['POST'])
@token_required
def initiate_claim(allocation_id):
    """Initiate a prize claim"""
    try:
        # Get the instant win record
        instant_win = InstantWin.query.get(allocation_id)
        if not instant_win:
            return jsonify({'error': 'Instant win not found'}), 404
            
        # Verify ownership
        if instant_win.ticket.user_id != request.current_user.id:
            return jsonify({'error': 'Not authorized to claim this prize'}), 403
            
        claim_info, error = ClaimService.initiate_claim(
            allocation_id=allocation_id,
            user_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(claim_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prize_bp.route('/instant-wins/<int:instant_win_id>/claims', methods=['POST'])
@token_required
def process_instant_win_claim(instant_win_id):
    """Process an instant win prize claim"""
    try:
        schema = PrizeClaimSchema()
        data = schema.load(request.get_json())
        
        result, error = ClaimService.process_instant_win_claim(
            instant_win_id=instant_win_id,
            user_id=request.current_user.id,
            claim_method=data['claim_method']
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(result)
        
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

@prize_bp.route('/instant-wins/<int:instant_win_id>/claim', methods=['POST'])
@token_required
def claim_instant_win(instant_win_id):
    """Process an instant win prize claim"""
    try:
        data = request.get_json()
        
        result, error = ClaimService.process_instant_win_claim(
            instant_win_id=instant_win_id,
            user_id=request.current_user.id,
            claim_method=data.get('claim_method')
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500