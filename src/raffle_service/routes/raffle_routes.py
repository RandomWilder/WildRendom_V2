# src/raffle_service/routes/raffle_routes.py
from flask import Blueprint, request, jsonify, current_app
from src.shared.auth import token_required, admin_required
from src.raffle_service.services.raffle_service import RaffleService
from src.raffle_service.services.ticket_service import TicketService
from src.raffle_service.services.purchase_limit_service import PurchaseLimitService
from src.raffle_service.services.instant_win_service import InstantWinService
from src.raffle_service.models.raffle import RaffleStatus
from src.raffle_service.models import InstantWin, Ticket
from src.user_service.services.user_service import UserService
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

        # Get raffle to check price
        raffle, error = RaffleService.get_raffle(raffle_id)
        if error:
            return jsonify({'error': error}), 400

        # Calculate total cost
        total_cost = raffle.ticket_price * quantity

        # Process credit transaction first
        user, error = UserService.update_credits(
            user_id=request.current_user.id,
            amount=total_cost,
            transaction_type='subtract',
            reference_type='raffle_purchase',
            reference_id=str(raffle_id),
            notes=f'Purchase of {quantity} tickets for Raffle ID: {raffle_id}'
        )
        
        if error:
            return jsonify({'error': error}), 400

        # Get the latest transaction ID for this user
        transactions = UserService.get_user_credit_transactions(request.current_user.id)[0]
        transaction_id = transactions[0]['id'] if transactions else None

        # Check purchase limits
        allowed, error_message = PurchaseLimitService.check_purchase_limit(
            user_id=request.current_user.id,
            raffle_id=raffle_id,
            requested_quantity=quantity
        )
        
        if not allowed:
            return jsonify({'error': error_message}), 400

        tickets, error = RaffleService.purchase_tickets(
            raffle_id=raffle_id,
            user_id=request.current_user.id,
            quantity=quantity,
            transaction_id=transaction_id
        )
        
        if error:
            # If ticket creation fails, refund the credits
            UserService.update_credits(
                user_id=request.current_user.id,
                amount=total_cost,
                transaction_type='add',
                reference_type='raffle_purchase_refund',
                reference_id=str(raffle_id),
                notes=f'Refund for failed ticket purchase in Raffle ID: {raffle_id}'
            )
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

@raffle_bp.route('/<int:raffle_id>/instant-wins', methods=['GET'])
@token_required
def get_raffle_instant_wins(raffle_id):
    """Get instant wins for a raffle"""
    try:
        instant_wins = InstantWin.query.filter_by(raffle_id=raffle_id).all()
        if not instant_wins:
            return jsonify([])
        return jsonify([win.to_dict() for win in instant_wins])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@raffle_bp.route('/<int:raffle_id>/tickets/reveal', methods=['POST'])
@token_required
def reveal_tickets(raffle_id):
    """Reveal purchased tickets"""
    try:
        data = request.get_json()
        ticket_ids = data.get('ticket_ids', [])
        
        if not ticket_ids:
            return jsonify({'error': 'No tickets specified for reveal'}), 400

        revealed_tickets, error = TicketService.reveal_tickets(
            user_id=request.current_user.id,
            ticket_ids=ticket_ids
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify([ticket.to_dict() for ticket in revealed_tickets]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@raffle_bp.route('/<int:raffle_id>/tickets/revealed', methods=['GET'])
@token_required
def get_revealed_tickets(raffle_id):
    """Get user's revealed tickets for a raffle"""
    try:
        tickets, error = TicketService.get_revealed_tickets(
            user_id=request.current_user.id,
            raffle_id=raffle_id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify([ticket.to_dict() for ticket in tickets]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@raffle_bp.route('/<int:raffle_id>/instant-wins/claim', methods=['POST'])
@token_required
def claim_instant_win(raffle_id):
    """Initiate claim for an instant win"""
    try:
        data = request.get_json()
        instant_win_id = data.get('instant_win_id')
        
        if not instant_win_id:
            return jsonify({'error': 'instant_win_id is required'}), 400
            
        # Verify ownership
        instant_win = InstantWin.query.get(instant_win_id)
        if not instant_win or instant_win.ticket.user_id != request.current_user.id:
            return jsonify({'error': 'Not authorized to claim this prize'}), 403

        claim_info, error = InstantWinService.initiate_claim(
            instant_win_id=instant_win_id,
            user_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(claim_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@raffle_bp.route('/<int:raffle_id>/instant-wins/status', methods=['GET'])
@token_required
def get_instant_win_status(raffle_id):
    """Get instant win status for user's tickets"""
    try:
        # Get user's tickets for this raffle that are instant wins
        instant_wins = InstantWin.query.join(Ticket).filter(
            InstantWin.raffle_id == raffle_id,
            Ticket.user_id == request.current_user.id
        ).all()
        
        return jsonify([win.to_dict() for win in instant_wins]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500