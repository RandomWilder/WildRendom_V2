# src/user_service/models/password_reset.py

from datetime import datetime, timezone
from src.shared import db

class PasswordReset(db.Model):
    """Model for tracking password reset requests"""
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)