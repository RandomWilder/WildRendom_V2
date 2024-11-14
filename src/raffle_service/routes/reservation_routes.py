from flask import Blueprint, request, jsonify
from src.shared.auth import token_required
from src.raffle_service.services.reservation_service import ReservationService

reservation_bp = Blueprint('reservation', __name__, url_prefix='/api/reservations')

@reservation_bp.route('/tickets', methods=['POST'])
@token_required
def create_reservation():
    """Create a ticket reservation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        raffle_id = data.get('raffle_id')
        quantity = data.get('quantity')

        if not raffle_id or not quantity:
            return jsonify({'error': 'raffle_id and quantity are required'}), 400

        if quantity <= 0:
            return jsonify({'error': 'quantity must be greater than 0'}), 400

        result, error = ReservationService.create_reservation(
            user_id=request.current_user.id,
            raffle_id=raffle_id,
            quantity=quantity
        )

        if error:
            return jsonify({'error': error}), 400

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500