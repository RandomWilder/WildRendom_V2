# src/raffle_service/schemas/raffle_schema.py
from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from datetime import datetime, timezone

from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from datetime import datetime, timezone

class DrawConfigurationSchema(Schema):
    """Schema for draw configuration"""
    number_of_draws = fields.Int(required=True, validate=validate.Range(min=1))
    distribution_type = fields.Str(required=True, validate=validate.OneOf(['single', 'split']))

class RaffleCreateSchema(Schema):
    """Schema for creating a new raffle"""
    title = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    description = fields.Str(validate=validate.Length(max=1000))
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    total_tickets = fields.Int(required=True, validate=validate.Range(min=1))
    max_tickets_per_user = fields.Int(required=True, validate=validate.Range(min=1))
    ticket_price = fields.Float(required=True, validate=validate.Range(min=0.01))
    prize_pool_id = fields.Int(required=True)
    draw_configuration = fields.Nested(DrawConfigurationSchema(), required=True)

    @validates_schema
    def validate_dates(self, data, **kwargs):
        """Validate date relationships"""
        if data['start_time'] >= data['end_time']:
            raise ValidationError('End time must be after start time')
            
        if data['start_time'] <= datetime.now(timezone.utc):
            raise ValidationError('Start time must be in the future')

    @validates_schema
    def validate_prize_pool(self, data, **kwargs):
        """Validate prize pool exists and is locked"""
        from src.prize_service.models import PrizePool, PoolStatus
        
        pool = PrizePool.query.get(data['prize_pool_id'])
        if not pool:
            raise ValidationError('Prize pool not found')
            
        if pool.status != PoolStatus.LOCKED.value:
            raise ValidationError('Prize pool must be locked')

class TicketPurchaseSchema(Schema):
    """Schema for ticket purchase"""
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=50)  # Limit max tickets per purchase
    )

class DrawExecutionSchema(Schema):
    """Schema for executing draws"""
    draw_count = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        default=1
    )

class StatusUpdateSchema(Schema):
    """Schema for status updates"""
    status = fields.Str(
        required=True,
        validate=validate.OneOf([
            'draft', 'coming_soon', 'active', 
            'inactive', 'sold_out', 'ended', 'cancelled'
        ])
    )

class VoidTicketSchema(Schema):
    """Schema for voiding tickets"""
    reason = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=255)
    )

class InstantWinSchema(Schema):
    """Schema for assigning instant wins"""
    count = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )

class RaffleResponseSchema(Schema):
    """Schema for raffle responses"""
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    description = fields.Str()
    total_tickets = fields.Int(required=True)
    ticket_price = fields.Float(required=True)
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    status = fields.Str(required=True)
    max_tickets_per_user = fields.Int()
    prize_pool_id = fields.Int()
    draw_configuration = fields.Nested(DrawConfigurationSchema())
    created_at = fields.DateTime()
    updated_at = fields.DateTime()