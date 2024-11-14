from flask import Blueprint, request, jsonify
from src.shared.auth import token_required
from src.raffle_service.services.ticket_service import TicketService
from src.raffle_service.models import Raffle
import logging

logger = logging.getLogger(__name__)

ticket_bp = Blueprint('tickets', __name__)

@ticket_bp.route('/api/raffles/tickets', methods=['GET'])
@token_required
def get_user_tickets():
    """Get all tickets for the current user"""
    try:
        user_id = request.current_user.id
        raffle_id = request.args.get('raffle_id', type=int)
        
        logger.debug(f"Fetching tickets for user_id: {user_id}, raffle_id: {raffle_id}")
        
        tickets, error = TicketService.get_user_tickets(user_id, raffle_id)
        
        if error:
            logger.error(f"Error fetching tickets for user {user_id}: {error}")
            return jsonify({'error': error}), 400
            
        logger.debug(f"Total tickets fetched: {len(tickets) if tickets else 0}")
            
        # Transform tickets to include raffle information
        response_tickets = []
        for ticket in tickets:
            logger.debug(f"Processing ticket: {ticket.ticket_id}, raffle_id: {ticket.raffle_id}")
            raffle = Raffle.query.get(ticket.raffle_id)
            logger.debug(f"Raffle found for ticket {ticket.ticket_id}: {raffle.title if raffle else 'Not found'}")
            
            ticket_data = {
                'id': ticket.ticket_id,
                'ticketId': ticket.ticket_id,
                'ticketNumber': ticket.ticket_number,
                'raffleId': ticket.raffle_id,
                'raffleTitle': raffle.title if raffle else 'Unknown Raffle',
                'userId': ticket.user_id,
                'purchaseTime': ticket.purchase_time.isoformat() if ticket.purchase_time else None,
                'endTime': raffle.end_time.isoformat() if raffle and raffle.end_time else None,
                'status': ticket.status,
                'isRevealed': ticket.is_revealed,
                'revealTime': ticket.reveal_time.isoformat() if ticket.reveal_time else None,
                'instantWin': ticket.instant_win,
                'transactionId': ticket.transaction_id
            }
            logger.debug(f"Transformed ticket data: {ticket_data}")
            response_tickets.append(ticket_data)

        logger.debug(f"Final response tickets count: {len(response_tickets)}")
        return jsonify(response_tickets), 200

    except Exception as e:
        logger.exception("Unexpected error in get_user_tickets")
        return jsonify({'error': str(e)}), 500

@ticket_bp.route('/api/raffles/<int:raffle_id>/tickets', methods=['POST'])
@token_required
def purchase_tickets(raffle_id: int):
    """Purchase tickets for a specific raffle"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        quantity = data.get('quantity')
        reservation_id = data.get('reservation_id')

        if not quantity or quantity <= 0:
            return jsonify({'error': 'Invalid quantity'}), 400

        purchased_tickets, error = TicketService.purchase_tickets(
            user_id=request.current_user.id,
            raffle_id=raffle_id,
            quantity=quantity,
            transaction_id=None  # Will be set by the service
        )

        if error:
            logger.error(f"Error purchasing tickets: {error}")
            return jsonify({'error': error}), 400

        response = {
            'tickets': [{
                'ticket_id': ticket.ticket_id,
                'ticket_number': ticket.ticket_number,
                'purchase_time': ticket.purchase_time.isoformat(),
                'status': ticket.status,
                'transaction_id': ticket.transaction_id
            } for ticket in purchased_tickets],
            'transaction': {
                'amount': len(purchased_tickets),  # This should be replaced with actual transaction amount
                'credits_remaining': 0  # This should be replaced with actual credits remaining
            }
        }

        return jsonify(response), 200

    except Exception as e:
        logger.exception("Unexpected error in purchase_tickets")
        return jsonify({'error': str(e)}), 500

@ticket_bp.route('/api/raffles/tickets/reveal', methods=['POST'])
@token_required
def reveal_tickets():
    """Reveal multiple tickets"""
    try:
        data = request.get_json()
        if not data or 'ticket_ids' not in data:
            return jsonify({'error': 'No ticket IDs provided'}), 400

        ticket_ids = data['ticket_ids']
        if not ticket_ids:
            return jsonify({'error': 'Empty ticket IDs list'}), 400

        revealed_tickets, error = TicketService.reveal_tickets(
            user_id=request.current_user.id,
            ticket_ids=ticket_ids
        )

        if error:
            logger.error(f"Error revealing tickets: {error}")
            return jsonify({'error': error}), 400

        response = [{
            'ticket_id': ticket.ticket_id,
            'ticket_number': ticket.ticket_number,
            'reveal_time': ticket.reveal_time.isoformat() if ticket.reveal_time else None,
            'instant_win': ticket.instant_win
        } for ticket in revealed_tickets]

        return jsonify(response), 200

    except Exception as e:
        logger.exception("Unexpected error in reveal_tickets")
        return jsonify({'error': str(e)}), 500

@ticket_bp.route('/api/raffles/<int:raffle_id>/tickets/<string:ticket_number>', methods=['GET'])
@token_required
def get_ticket(raffle_id: int, ticket_number: str):
    """Get specific ticket information"""
    try:
        ticket, error = TicketService.get_ticket_by_number(raffle_id, ticket_number)
        
        if error:
            return jsonify({'error': error}), 404

        raffle = Raffle.query.get(ticket.raffle_id)
        response = {
            'id': ticket.ticket_id,
            'ticketId': ticket.ticket_id,
            'ticketNumber': ticket.ticket_number,
            'raffleId': ticket.raffle_id,
            'raffleTitle': raffle.title if raffle else 'Unknown Raffle',
            'userId': ticket.user_id,
            'purchaseTime': ticket.purchase_time.isoformat() if ticket.purchase_time else None,
            'endTime': raffle.end_time.isoformat() if raffle and raffle.end_time else None,
            'status': ticket.status,
            'isRevealed': ticket.is_revealed,
            'revealTime': ticket.reveal_time.isoformat() if ticket.reveal_time else None,
            'instantWin': ticket.instant_win,
            'transactionId': ticket.transaction_id
        }

        return jsonify(response), 200

    except Exception as e:
        logger.exception("Unexpected error in get_ticket")
        return jsonify({'error': str(e)}), 500