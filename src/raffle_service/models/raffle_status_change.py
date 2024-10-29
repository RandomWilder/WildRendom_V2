# src/raffle_service/models/raffle_status_change.py
from datetime import datetime, timezone
from src.shared import db

class RaffleStatusChange(db.Model):
    """Track raffle status changes for audit and history"""
    __tablename__ = 'raffle_status_changes'

    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffles.id'), nullable=False)
    previous_status = db.Column(db.String(20), nullable=False)
    new_status = db.Column(db.String(20), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    raffle = db.relationship('Raffle', backref=db.backref('status_changes', lazy='dynamic'))
    changed_by = db.relationship('User', backref=db.backref('raffle_status_changes', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'raffle_id': self.raffle_id,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'changed_by_id': self.changed_by_id,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }