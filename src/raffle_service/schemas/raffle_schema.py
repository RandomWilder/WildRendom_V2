# src/raffle_service/schemas/raffle_schema.py
from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from datetime import datetime, timezone

class RaffleCreateSchema(Schema):
    """Schema for creating a new raffle"""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=100)
    )
    description = fields.Str(
        required=False,
        validate=validate.Length(max=1000)
    )
    total_tickets = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
    ticket_price = fields.Float(
        required=True,
        validate=validate.Range(min=0)
    )
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    total_prize_count = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
    instant_win_count = fields.Int(
        required=False,
        validate=validate.Range(min=0),
        default=0
    )
    prize_structure = fields.Dict(
        required=False,
        allow_none=True
    )

    @validates_schema
    def validate_dates(self, data, **kwargs):
        """Validate date relationships"""
        if data['start_time'] >= data['end_time']:
            raise ValidationError('End time must be after start time')
            
        if data['start_time'] <= datetime.now(timezone.utc):
            raise ValidationError('Start time must be in the future')

        if 'instant_win_count' in data and data['instant_win_count'] > data['total_prize_count']:
            raise ValidationError('Instant win count cannot exceed total prize count')

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
            'paused', 'sold_out', 'ended', 'cancelled'
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