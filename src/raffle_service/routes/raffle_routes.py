from flask import Blueprint, request, jsonify, current_app
from src.shared.auth import token_required, admin_required
from src.raffle_service.services.raffle_service import RaffleService
from src.raffle_service.services.ticket_service import TicketService
from src.raffle_service.services.purchase_limit_service import PurchaseLimitService
from src.raffle_service.models.raffle import RaffleStatus
from datetime import datetime
from marshmallow import ValidationError

raffle_bp = Blueprint('raffle', __name__, url_prefix='/api/raffles')

@raffle_bp.route('/', methods=['GET'])
def list_raffles():
    """List all raffles"""
    raffles, error = RaffleService.get_raffles_by_status(RaffleStatus.ACTIVE)
    if error:
        return jsonify({'error': error}), 400
    return jsonify([raffle.to_dict() for raffle in raffles])

@raffle_bp.route('/<int:raffle_id>', methods=['GET'])
def get_raffle(raffle_id):
    """Get raffle details"""
    raffle, error = RaffleService.get_raffle(raffle_id)
    if error:
        return jsonify({'error': error}), 404
    return jsonify(raffle.to_dict())

@raffle_bp.route('/<int:raffle_id>/stats', methods=['GET'])
def get_raffle_stats(raffle_id):
    """Get raffle statistics"""
    stats, error = TicketService.get_raffle_statistics(raffle_id)
    if error:
        return jsonify({'error': error}), 404
        
    # Add user-specific stats if authenticated
    current_user = getattr(request, 'current_user', None)
    if current_user:
        user_stats, _ = PurchaseLimitService.get_user_stats(current_user.id, raffle_id)
        if user_stats:
            stats['user_tickets_purchased'] = user_stats.tickets_purchased
            stats['user_remaining_limit'] = (
                current_app.config['RAFFLE'].MAX_TICKETS_PER_USER - 
                user_stats.tickets_purchased
            )
    
    return jsonify(stats)

@raffle_bp.route('/<int:raffle_id>/tickets', methods=['POST'])
@token_required
def purchase_tickets(raffle_id):
    """Purchase tickets for a raffle"""
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        # Validate purchase quantity
        raffle_config = current_app.config['RAFFLE']
        if quantity < raffle_config.MIN_TICKETS_PER_PURCHASE:
            return jsonify({
                'error': f'Minimum purchase is {raffle_config.MIN_TICKETS_PER_PURCHASE} ticket(s)'
            }), 400
            
        if quantity > raffle_config.MAX_TICKETS_PER_TRANSACTION:
            return jsonify({
                'error': f'Maximum purchase is {raffle_config.MAX_TICKETS_PER_TRANSACTION} tickets per transaction'
            }), 400

        # Check purchase limits
        allowed, error_message = PurchaseLimitService.check_purchase_limit(
            user_id=request.current_user.id,
            raffle_id=raffle_id,
            requested_quantity=quantity,
            max_tickets=raffle_config.MAX_TICKETS_PER_TRANSACTION
        )
        
        if not allowed:
            return jsonify({'error': error_message}), 400

        # In a real application, we'd handle the credit transaction here
        transaction_id = 1  # This should come from credit transaction
        
        tickets, error = RaffleService.purchase_tickets(
            raffle_id=raffle_id,
            user_id=request.current_user.id,
            quantity=quantity,
            transaction_id=transaction_id
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        # Update purchase count after successful purchase
        PurchaseLimitService.update_purchase_count(
            user_id=request.current_user.id,
            raffle_id=raffle_id,
            quantity=quantity
        )
        
        return jsonify([ticket.to_dict() for ticket in tickets]), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@raffle_bp.route('/tickets', methods=['GET'])
@token_required
def get_my_tickets():
    """Get current user's tickets"""
    raffle_id = request.args.get('raffle_id', type=int)
    tickets, error = TicketService.get_user_tickets(
        user_id=request.current_user.id,
        raffle_id=raffle_id
    )
    
    if error:
        return jsonify({'error': error}), 400
        
    return jsonify([ticket.to_dict() for ticket in tickets])