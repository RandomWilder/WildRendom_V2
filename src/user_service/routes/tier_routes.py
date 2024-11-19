# src/user_service/routes/tier_routes.py

from flask import Blueprint, request, jsonify
from src.shared.auth import token_required, admin_required
from src.user_service.services.tier_service import TierService
import logging

logger = logging.getLogger(__name__)

tier_bp = Blueprint('tiers', __name__, url_prefix='/api/users/tiers')

@tier_bp.route('/test', methods=['GET'])
def test_tier_route():
    """Test endpoint to verify routing"""
    return jsonify({'message': 'Tier routes working'}), 200

@tier_bp.route('/my-tier', methods=['GET'])
@token_required
def get_my_tier():
    """Get current user's tier information"""
    try:
        tier_info, error = TierService.get_user_tier(request.current_user.id)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(tier_info)
        
    except Exception as e:
        logger.error(f"Error in get_my_tier: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@tier_bp.route('/progress', methods=['GET'])
@token_required
def get_tier_progress():
    """Get current user's progress towards next tier"""
    try:
        progress, error = TierService.get_tier_progress(request.current_user.id)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(progress)
        
    except Exception as e:
        logger.error(f"Error in get_tier_progress: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tier_bp.route('/history', methods=['GET'])
@token_required
def get_tier_history():
    """Get current user's tier change history"""
    try:
        history, error = TierService.get_tier_history(request.current_user.id)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(history)
        
    except Exception as e:
        logger.error(f"Error in get_tier_history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tier_bp.route('/admin/users/<int:user_id>/tier', methods=['GET'])
@admin_required
def get_user_tier(user_id):
    """Admin endpoint to get user's tier information"""
    try:
        tier_info, error = TierService.get_user_tier(user_id)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(tier_info)
        
    except Exception as e:
        logger.error(f"Error in get_user_tier: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tier_bp.route('/admin/users/<int:user_id>/evaluate', methods=['POST'])
@admin_required
def evaluate_user_tier(user_id):
    """Admin endpoint to trigger tier evaluation"""
    try:
        changed, error = TierService.evaluate_user_tier(user_id)
        if error:
            return jsonify({'error': error}), 400
            
        tier_info, _ = TierService.get_user_tier(user_id)
        return jsonify({
            'tier_changed': changed,
            'current_tier': tier_info
        })
        
    except Exception as e:
        logger.error(f"Error in evaluate_user_tier: {str(e)}")
        return jsonify({'error': str(e)}), 500