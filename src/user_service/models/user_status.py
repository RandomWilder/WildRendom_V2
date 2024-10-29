from datetime import datetime, timezone
from src.shared import db

class UserStatusChange(db.Model):
    """Track user status changes"""
    __tablename__ = 'user_status_changes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    previous_status = db.Column(db.Boolean, nullable=False)
    new_status = db.Column(db.Boolean, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'changed_by_id': self.changed_by_id,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat()
        }