from datetime import datetime, timezone
from src.shared import db

class UserActivity(db.Model):
    """Track user activities and system interactions"""
    __tablename__ = 'user_activities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # login, logout, profile_update, etc.
    ip_address = db.Column(db.String(45))  # IPv4/IPv6 address
    user_agent = db.Column(db.String(255))  # Browser/client info
    status = db.Column(db.String(20))  # success, failed, blocked, etc.
    details = db.Column(db.JSON)  # Additional activity-specific details
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'details': self.details,
            'created_at': self.created_at.isoformat()
        }