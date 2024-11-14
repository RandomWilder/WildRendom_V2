# src/raffle_service/routes/payment_routes.py

from flask import Blueprint, request, jsonify
from src.shared.auth import token_required
from src.raffle_service.services.payment_service import PaymentService

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payments')

@payment_bp.route('/intents', methods=['POST'])
@token_required
def create_payment_intent():
    """Create a payment intent for a reservation"""
    try:
        data = request.get_json()
        reservation_id = data.get('reservation_id')
        
        if not reservation_id:
            return jsonify({'error': 'reservation_id is required'}), 400

        result, error = PaymentService.create_payment_intent(
            reservation_id=reservation_id,
            user_id=request.current_user.id
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/intents/<intent_id>/confirm', methods=['POST'])
@token_required
def confirm_payment(intent_id):
    """Confirm payment and finalize ticket purchase"""
    try:
        result, error = PaymentService.confirm_payment(
            payment_intent_id=intent_id,
            user_id=request.current_user.id
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500