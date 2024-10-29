from marshmallow import Schema, fields, validate, validates_schema, ValidationError, EXCLUDE
from typing import Optional

class UserBaseSchema(Schema):
    """Base schema with common user fields"""
    class Meta:
        unknown = EXCLUDE  # Ignore unknown fields

    username = fields.Str(
        required=True, 
        validate=validate.Length(min=3, max=64)
    )
    email = fields.Email(required=True)
    first_name = fields.Str(validate=validate.Length(max=64))
    last_name = fields.Str(validate=validate.Length(max=64))

class UserRegistrationSchema(UserBaseSchema):
    """Schema for user registration"""
    class Meta:
        unknown = EXCLUDE

    password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128),
        load_only=True  # Password will not be included in serialized output
    )

    @validates_schema
    def validate_password_strength(self, data, **kwargs):
        """Validate password meets security requirements"""
        if 'password' in data:
            password = data['password']
            errors = []
            
            if not any(c.isupper() for c in password):
                errors.append("Password must contain at least one uppercase letter")
            if not any(c.islower() for c in password):
                errors.append("Password must contain at least one lowercase letter")
            if not any(c.isdigit() for c in password):
                errors.append("Password must contain at least one number")
            if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
                errors.append("Password must contain at least one special character")
                
            if errors:
                raise ValidationError({'password': errors})

class UserLoginSchema(Schema):
    """Schema for user login"""
    class Meta:
        unknown = EXCLUDE

    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

class UserUpdateSchema(Schema):
    """Schema for user profile updates"""
    class Meta:
        unknown = EXCLUDE

    email = fields.Email(required=False)
    first_name = fields.Str(required=False, validate=validate.Length(max=64))
    last_name = fields.Str(required=False, validate=validate.Length(max=64))
    password = fields.Str(
        required=False,
        validate=validate.Length(min=8, max=128),
        load_only=True
    )
    current_password = fields.Str(load_only=True, required=False)

    @validates_schema
    def validate_password_update(self, data, **kwargs):
        if 'password' in data and not data.get('current_password'):
            raise ValidationError(
                'current_password is required when updating password'
            )

class CreditUpdateSchema(Schema):
    """Schema for credit balance updates"""
    class Meta:
        unknown = EXCLUDE

    amount = fields.Float(required=True)
    transaction_type = fields.Str(
        required=True,
        validate=validate.OneOf(['add', 'subtract'])
    )
    reference_type = fields.Str(required=False)
    reference_id = fields.Str(required=False)
    notes = fields.Str(required=False)

    @validates_schema
    def validate_amount(self, data, **kwargs):
        if data['amount'] <= 0:
            raise ValidationError('Amount must be greater than 0')

class UserResponseSchema(Schema):
    """Schema for user responses"""
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(required=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    first_name = fields.Str()
    last_name = fields.Str()
    site_credits = fields.Float()
    is_active = fields.Bool()
    is_verified = fields.Bool()
    created_at = fields.DateTime()
    last_login = fields.DateTime()