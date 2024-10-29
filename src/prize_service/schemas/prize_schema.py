# src/prize_service/schemas/prize_schema.py

from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from src.prize_service.models import PrizeType, PrizeStatus, PrizeTier, ClaimStatus

class PrizeCreateSchema(Schema):
    """Schema for creating a new prize"""
    name = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    description = fields.Str(validate=validate.Length(max=1000))
    type = fields.Str(required=True, validate=validate.OneOf([t.value for t in PrizeType]))
    custom_type = fields.Str(validate=validate.Length(max=50))
    tier = fields.Str(validate=validate.OneOf([t.value for t in PrizeTier]))
    
    retail_value = fields.Decimal(required=True, places=2)
    cash_value = fields.Decimal(required=True, places=2)
    credit_value = fields.Decimal(required=True, places=2)
    
    total_quantity = fields.Int(validate=validate.Range(min=0))
    min_threshold = fields.Int(validate=validate.Range(min=0))
    win_limit_per_user = fields.Int(validate=validate.Range(min=1))
    win_limit_period_days = fields.Int(validate=validate.Range(min=1))

class PrizePoolCreateSchema(Schema):
    """Schema for creating a prize pool"""
    name = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    description = fields.Str(validate=validate.Length(max=1000))
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    budget_limit = fields.Decimal(places=2)
    allocation_rules = fields.Dict()
    win_limits = fields.Dict()
    eligibility_rules = fields.Dict()

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if data['start_date'] >= data['end_date']:
            raise ValidationError('end_date must be after start_date')

class PrizeClaimSchema(Schema):
    """Schema for prize claims"""
    claim_method = fields.Str(required=True, validate=validate.OneOf(['prize', 'cash', 'credit']))
    shipping_address = fields.Dict(required=False)  # Only for physical prizes

class PrizeAllocationCreateSchema(Schema):
    """Schema for creating prize allocations"""
    prize_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    allocation_rules = fields.Dict(required=False)
    # Remove pool_id as it comes from the URL

class PrizeResponseSchema(Schema):
    """Schema for prize responses"""
    id = fields.Int()
    name = fields.Str()
    description = fields.Str()
    type = fields.Str()
    custom_type = fields.Str()
    tier = fields.Str()
    retail_value = fields.Decimal(places=2)
    cash_value = fields.Decimal(places=2)
    credit_value = fields.Decimal(places=2)
    total_quantity = fields.Int()
    available_quantity = fields.Int()
    status = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class ClaimResponseSchema(Schema):
    """Schema for claim responses"""
    allocation_id = fields.Int()
    status = fields.Str()
    claim_method = fields.Str()
    value_claimed = fields.Decimal(places=2)
    claimed_at = fields.DateTime()
    deadline = fields.DateTime()