# src/user_service/schemas/password_schema.py

from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class PasswordResetRequestSchema(Schema):
    """Schema for password reset request"""
    email = fields.Email(required=True)

class PasswordResetSchema(Schema):
    """Schema for password reset"""
    token = fields.Str(required=True)
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128)
    )
    
    @validates_schema
    def validate_password_strength(self, data, **kwargs):
        """Validate password meets security requirements"""
        password = data['new_password']
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
            raise ValidationError({'new_password': errors})

class PasswordChangeSchema(Schema):
    """Schema for password change"""
    current_password = fields.Str(required=True)
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128)
    )
    
    @validates_schema
    def validate_password_strength(self, data, **kwargs):
        """Validate password meets security requirements"""
        password = data['new_password']
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
            raise ValidationError({'new_password': errors})