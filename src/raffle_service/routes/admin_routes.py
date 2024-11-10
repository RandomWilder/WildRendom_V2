# src/raffle_service/routes/admin_routes.py
import logging
from flask import Blueprint, request, jsonify, current_app
from src.shared.auth import admin_required
from src.raffle_service.services.raffle_service import RaffleService
from src.raffle_service.services.ticket_service import TicketService
from src.raffle_service.services.instant_win_service import InstantWinService
from src.raffle_service.services.draw_service import DrawService
from src.raffle_service.schemas.raffle_schema import RaffleCreateSchema
from marshmallow import ValidationError
from src.raffle_service.models.raffle import RaffleStatus
from src.raffle_service.models.ticket import Ticket
from src.raffle_service.models import InstantWin
from src.user_service.models.user import User
from src.raffle_service.services.ticket_service import TicketService
from src.raffle_service.services.purchase_limit_service import PurchaseLimitService

raffle_admin_bp = Blueprint('raffle_admin', __name__, url_prefix='/api/admin/raffles')
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

@raffle_admin_bp.route('/raffles/create', methods=['POST'])
@admin_required
def create_raffle():
    """Create a new raffle"""
    try:
        # Validate input using schema
        schema = RaffleCreateSchema()
        data = schema.load(request.get_json())
        
        raffle, error = RaffleService.create_raffle(
            data=data,
            admin_id=request.current_user.id
        )
        
        if error:
            logger.error(f"Error creating raffle: {error}")
            return jsonify({'error': error}), 400
            
        # Response is already formatted according to API spec by the service
        return jsonify(raffle), 201
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e.messages)}")
        return jsonify({'error': e.messages}), 400
    except Exception as e:
        logger.error(f"Unexpected error creating raffle: {str(e)}")
        return jsonify({'error': str(e)}), 500

@raffle_admin_bp.route('/raffles/<int:raffle_id>/status', methods=['PUT'])
@admin_required
def update_raffle_status(raffle_id):
    """Update raffle status"""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': "Status is required"}), 400

        current_raffle = RaffleService.get_raffle(raffle_id)[0]
        if not current_raffle:
            return jsonify({'error': "Raffle not found"}), 404

        logger.info(f"Updating raffle {raffle_id} status: {current_raffle.status} -> {data['status']}")
        
        try:
            new_status = RaffleStatus(data['status'])
        except ValueError:
            return jsonify({
                'error': f"Invalid status. Valid statuses are: {[s.value for s in RaffleStatus]}"
            }), 400

        raffle, error = RaffleService.update_raffle_status(
            raffle_id=raffle_id,
            new_status=new_status,
            admin_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400

        return jsonify(raffle.to_dict())
        
    except Exception as e:
        logger.error(f"Unexpected error in update_raffle_status: {str(e)}")
        return jsonify({'error': f"Server error: {str(e)}"}), 500

@raffle_admin_bp.route('/raffles/<int:raffle_id>/draw', methods=['POST'])
@admin_required
def execute_draw(raffle_id):
    """Execute prize draw"""
    try:
        data = request.get_json()
        draw_count = data.get('draw_count', 1)
        
        if draw_count > 1:
            winners, error = DrawService.execute_multiple_draws(
                raffle_id=raffle_id,
                admin_id=request.current_user.id,
                number_of_draws=draw_count
            )
        else:
            winner, error = DrawService.execute_draw(
                raffle_id=raffle_id,
                admin_id=request.current_user.id
            )
            winners = [winner] if winner else []
            
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify([ticket.to_dict() for ticket in winners])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@raffle_admin_bp.route('/raffles/<int:raffle_id>/tickets', methods=['GET'])
@admin_required
def get_raffle_tickets(raffle_id):
    """Get all tickets for a raffle with detailed information"""
    try:
        tickets = Ticket.query.filter_by(raffle_id=raffle_id).all()
        
        if not tickets:
            return jsonify({'error': 'No tickets found for this raffle'}), 404
            
        ticket_details = []
        for ticket in tickets:
            detail = ticket.to_dict()
            detail.update({
                'paid': ticket.transaction_id is not None,
                'user': None  # Will be populated if ticket is sold
            })
            
            if ticket.user_id:
                user = User.query.get(ticket.user_id)
                if user:
                    detail['user'] = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
            
            ticket_details.append(detail)
            
        return jsonify({
            'total_count': len(tickets),
            'tickets': ticket_details
        })
        
    except Exception as e:
        logger.error(f"Error getting raffle tickets: {str(e)}")
        return jsonify({'error': str(e)}), 500

@raffle_admin_bp.route('/tickets/<int:ticket_id>/void', methods=['POST'])
@admin_required
def void_ticket(ticket_id):
    """Void a ticket"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'Administrative action')
        
        ticket, error = TicketService.void_ticket(
            ticket_id=ticket_id,
            admin_id=request.current_user.id,
            reason=reason
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(ticket.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@raffle_admin_bp.route('/raffles/<int:raffle_id>/instant-wins', methods=['POST'])
@admin_required
def assign_instant_wins(raffle_id):
    """Assign instant win tickets"""
    try:
        data = request.get_json()
        count = data.get('count', 0)
        
        if count <= 0:
            return jsonify({'error': 'Count must be greater than 0'}), 400
            
        instant_wins, error = InstantWinService.allocate_instant_wins(
            raffle_id=raffle_id,
            count=count
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify([win.to_dict() for win in instant_wins]), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@raffle_admin_bp.route('/raffles/<int:raffle_id>/instant-wins', methods=['GET'])
@admin_required
def get_instant_wins(raffle_id):
    """Get all instant wins for a raffle"""
    try:
        instant_wins = InstantWin.query.filter_by(raffle_id=raffle_id).all()
        return jsonify([win.to_dict() for win in instant_wins])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@raffle_admin_bp.route('/raffles/<int:raffle_id>', methods=['PUT'])
@admin_required
def update_raffle(raffle_id):
    """Update raffle details"""
    try:
        data = request.get_json()
        
        raffle, error = RaffleService.update_raffle(
            raffle_id=raffle_id,
            data=data,
            admin_id=request.current_user.id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(raffle.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@raffle_admin_bp.route('/raffles/<int:raffle_id>/fix-stats', methods=['POST'])
@admin_required
def fix_raffle_stats(raffle_id):
    """Fix user stats discrepancy for a raffle"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
            
        success, error = TicketService.fix_purchase_count_discrepancy(
            user_id=user_id,
            raffle_id=raffle_id
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        # Get updated stats
        fixed_stats, _ = PurchaseLimitService.get_user_stats(user_id, raffle_id)
        if not fixed_stats:
            return jsonify({'error': 'Could not retrieve updated stats'}), 500
            
        return jsonify({
            'success': True,
            'fixed_stats': {
                'user_id': user_id,
                'raffle_id': raffle_id,
                'tickets_purchased': fixed_stats.tickets_purchased,
                'last_purchase_time': fixed_stats.last_purchase_time.isoformat() if fixed_stats.last_purchase_time else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error fixing raffle stats: {str(e)}")
        return jsonify({'error': str(e)}), 500