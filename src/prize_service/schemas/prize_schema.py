# src/prize_service/schemas/prize_schema.py

from marshmallow import Schema, fields, validate, validates_schema, ValidationError, EXCLUDE
from src.prize_service.models import PrizeType, PrizeStatus, PrizeTier

class PrizeCreateSchema(Schema):
    """Schema for creating a new prize template"""
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    description = fields.Str(validate=validate.Length(max=1000))
    type = fields.Str(required=True, validate=validate.OneOf(['Instant_Win', 'Draw_Win']))
    tier = fields.Str(required=True, validate=validate.OneOf(['platinum', 'gold', 'silver', 'bronze']))
    retail_value = fields.Decimal(required=True, places=2)
    cash_value = fields.Decimal(required=True, places=2)
    credit_value = fields.Decimal(required=True, places=2)
    expiry_days = fields.Int(validate=validate.Range(min=1), default=7)
    claim_deadline_hours = fields.Int(validate=validate.Range(min=1))
    auto_claim_credit = fields.Boolean(default=False)

class PrizeUpdateSchema(Schema):
    """Schema for updating a prize template"""
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(validate=validate.Length(min=3, max=100))
    retail_value = fields.Decimal(places=2)
    cash_value = fields.Decimal(places=2)
    credit_value = fields.Decimal(places=2)
    expiry_days = fields.Int(validate=validate.Range(min=1))
    claim_deadline_hours = fields.Int(validate=validate.Range(min=1))
    auto_claim_credit = fields.Boolean()

class PrizePoolCreateSchema(Schema):
    """Schema for creating a prize pool"""
    class Meta:
        unknown = EXCLUDE
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=False, allow_none=True)

class PrizePoolResponseSchema(Schema):
    """Schema for prize pool responses"""
    pool_id = fields.Int(attribute='id')
    name = fields.Str()
    description = fields.Str(allow_none=True)
    total_instances = fields.Int()
    values = fields.Dict(keys=fields.Str(), values=fields.Float())
    status = fields.Str()

class PrizeInstanceSchema(Schema):
    """Schema for prize instance details"""
    class Meta:
        unknown = EXCLUDE

    instance_id = fields.Str(required=True)
    prize_id = fields.Int(required=True)
    individual_odds = fields.Float(required=True)
    status = fields.Str(required=True)
    values = fields.Dict(keys=fields.Str(), values=fields.Float())
    claim_attempts = fields.Int()
    claim_deadline = fields.DateTime()
    claimed_at = fields.DateTime()

class PrizeAllocationCreateSchema(Schema):
    """Schema for allocating prizes to a pool"""
    class Meta:
        unknown = EXCLUDE

    prize_template_id = fields.Int(required=True)
    instance_count = fields.Int(required=True, validate=validate.Range(min=1))
    collective_odds = fields.Float(required=True, validate=validate.Range(min=0, max=100))

    @validates_schema
    def validate_odds(self, data, **kwargs):
        """Ensure odds are valid"""
        if data['collective_odds'] <= 0:
            raise ValidationError('collective_odds must be greater than 0')
        if data['collective_odds'] > 100:
            raise ValidationError('collective_odds cannot exceed 100')

class PrizeResponseSchema(Schema):
    """Schema for prize responses"""
    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    prize_id = fields.Int()
    name = fields.Str()
    description = fields.Str()
    type = fields.Str()
    tier = fields.Str()
    retail_value = fields.Decimal(places=2)
    cash_value = fields.Decimal(places=2)
    credit_value = fields.Decimal(places=2)
    status = fields.Str()
    total_allocated = fields.Int()
    total_claimed = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class PoolStatsResponseSchema(Schema):
    """Schema for pool statistics response"""
    class Meta:
        unknown = EXCLUDE

    total_instances = fields.Int()
    by_type = fields.Dict(keys=fields.Str(), values=fields.Dict())
    values = fields.Dict(keys=fields.Str(), values=fields.Float())
    claimed_values = fields.Dict(keys=fields.Str(), values=fields.Float())

class ClaimResponseSchema(Schema):
    """Schema for claim responses"""
    class Meta:
        unknown = EXCLUDE

    instance_id = fields.Str()
    status = fields.Str()
    claim_method = fields.Str()
    value_claimed = fields.Decimal(places=2)
    claim_attempts = fields.Int()
    claimed_at = fields.DateTime()
    deadline = fields.DateTime()

class PrizeClaimSchema(Schema):
    """Schema for prize claim requests"""
    class Meta:
        unknown = EXCLUDE

    claim_method = fields.Str(
        required=True, 
        validate=validate.OneOf(['credit', 'cash', 'digital'])
    )
    value_type = fields.Str(
        required=False,
        validate=validate.OneOf(['retail', 'cash', 'credit'])
    )

    @validates_schema
    def validate_claim_method(self, data, **kwargs):
        """Validate claim method matches value type if provided"""
        if data.get('claim_method') == 'credit' and data.get('value_type') not in [None, 'credit']:
            raise ValidationError("Credit claims must use credit value type")
        if data.get('claim_method') == 'cash' and data.get('value_type') not in [None, 'cash']:
            raise ValidationError("Cash claims must use cash value type")