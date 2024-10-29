from flask import Blueprint, request, jsonify
from src.user_service.schemas.user_schema import (
    UserRegistrationSchema, 
    UserLoginSchema,
    UserUpdateSchema,
    CreditUpdateSchema
)
from src.user_service.services.user_service import UserService
from marshmallow import ValidationError
from src.shared.auth import token_required, create_token, admin_required
from src.user_service.services.activity_service import ActivityService
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        schema = UserRegistrationSchema()
        user_data = schema.load(request.get_json())
        
        user, error = UserService.create_user(user_data)
        if error:
            ActivityService.log_activity(
                user_id=None,
                activity_type='registration',
                request=request,
                status='failed',
                details={'error': error, 'username': user_data.get('username')}
            )
            return jsonify({'error': error}), 400
        
        ActivityService.log_activity(
            user_id=user.id,
            activity_type='registration',
            request=request,
            status='success'
        )
        return jsonify(user.to_dict()), 201
        
    except ValidationError as e:
        ActivityService.log_activity(
            user_id=None,
            activity_type='registration',
            request=request,
            status='failed',
            details={'error': e.messages}
        )
        return jsonify({'error': e.messages}), 400

@user_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    try:
        schema = UserLoginSchema()
        login_data = schema.load(request.get_json())
        
        user, error = UserService.authenticate_user(
            login_data['username'],
            login_data['password']
        )
        if error:
            ActivityService.log_activity(
                user_id=None,
                activity_type='login',
                request=request,
                status='failed',
                details={'error': error, 'username': login_data['username']}
            )
            return jsonify({'error': error}), 401
        
        # Create authentication token
        token = create_token(user.id)
        
        ActivityService.log_activity(
            user_id=user.id,
            activity_type='login',
            request=request,
            status='success'
        )
        
        return jsonify({
            'user': user.to_dict(),
            'token': token
        }), 200
        
    except ValidationError as e:
        ActivityService.log_activity(
            user_id=None,
            activity_type='login',
            request=request,
            status='failed',
            details={'error': e.messages}
        )
        return jsonify({'error': e.messages}), 400


@user_bp.route('/profile/<int:user_id>', methods=['PUT'])
@token_required
def update_profile(user_id):
    """Update user profile"""
    # Verify user is updating their own profile
    if request.current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        schema = UserUpdateSchema()
        update_data = schema.load(request.get_json())
        
        user, error = UserService.update_user(user_id, update_data)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(user.to_dict()), 200
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400

@user_bp.route('/credits/<int:user_id>', methods=['POST'])
@token_required
def update_credits(user_id):
    """Update user credits"""
    try:
        # Verify user is updating their own credits or is admin
        if request.current_user.id != user_id and not request.current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        schema = CreditUpdateSchema()
        credit_data = schema.load(data)
        
        # Get additional transaction details
        reference_type = data.get('reference_type')
        reference_id = data.get('reference_id')
        notes = data.get('notes')
        
        user, error = UserService.update_credits(
            user_id=user_id,
            amount=credit_data['amount'],
            transaction_type=credit_data['transaction_type'],
            admin_id=request.current_user.id if request.current_user.is_admin else None,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(user.to_dict()), 200
        
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@user_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user details"""
    return jsonify(request.current_user.to_dict())

@user_bp.route('/admin/users', methods=['GET'])
@admin_required  # Using our new admin decorator
def get_all_users():
    """Admin route to get all users"""
    try:
        users = UserService.get_all_users()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@user_bp.route('/admin/users/<int:user_id>/status', methods=['POST'])
@admin_required
def update_user_status(user_id):
    """Admin route to update user status"""
    try:
        data = request.get_json()
        if not isinstance(data.get('is_active'), bool):
            return jsonify({'error': 'is_active must be a boolean'}), 400
        if not data.get('reason'):
            return jsonify({'error': 'reason is required'}), 400
            
        user, error = UserService.update_user_status(
            user_id=user_id,
            admin_id=request.current_user.id,
            is_active=data['is_active'],
            reason=data['reason']
        )
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@user_bp.route('/credits/<int:user_id>/history', methods=['GET'])
@token_required
def get_credit_history(user_id):
    """Get credit transaction history for a user"""
    # Verify user is viewing their own history or is admin
    if request.current_user.id != user_id and not request.current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    transactions, error = UserService.get_user_credit_transactions(user_id)
    if error:
        return jsonify({'error': error}), 400
        
    return jsonify(transactions), 200

@user_bp.route('/admin/credits/history', methods=['GET'])
@admin_required
def get_all_credit_history():
    """Admin route to get all credit transactions"""
    transactions, error = UserService.get_all_credit_transactions()
    if error:
        return jsonify({'error': error}), 400
        
    return jsonify(transactions), 200

@user_bp.route('/activities/<int:user_id>', methods=['GET'])
@token_required
def get_user_activities(user_id):
    """Get activity history for a user"""
    # Verify user is viewing their own activities or is admin
    if request.current_user.id != user_id and not request.current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get query parameters
    activity_type = request.args.get('activity_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Convert date strings to datetime objects if provided
    if start_date:
        start_date = datetime.fromisoformat(start_date)
    if end_date:
        end_date = datetime.fromisoformat(end_date)
    
    activities, error = ActivityService.get_user_activities(
        user_id,
        activity_type=activity_type,
        start_date=start_date,
        end_date=end_date
    )
    
    if error:
        return jsonify({'error': error}), 400
        
    return jsonify([activity.to_dict() for activity in activities]), 200

@user_bp.route('/admin/activities', methods=['GET'])
@admin_required
def get_all_activities():
    """Admin route to get all user activities"""
    activity_type = request.args.get('activity_type')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Convert date strings to datetime objects if provided
    if start_date:
        start_date = datetime.fromisoformat(start_date)
    if end_date:
        end_date = datetime.fromisoformat(end_date)
    
    activities, error = ActivityService.get_all_activities(
        activity_type=activity_type,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
    if error:
        return jsonify({'error': error}), 400
        
    return jsonify([activity.to_dict() for activity in activities]), 200