from datetime import datetime, timezone
from src.shared import db

class UserRaffleStats(db.Model):
    """Track user participation in raffles"""
    __tablename__ = 'user_raffle_stats'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffles.id'), nullable=False)
    tickets_purchased = db.Column(db.Integer, default=0)
    last_purchase_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    # Unique constraint to ensure one record per user per raffle
    __table_args__ = (
        db.UniqueConstraint('user_id', 'raffle_id', name='unique_user_raffle'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'raffle_id': self.raffle_id,
            'tickets_purchased': self.tickets_purchased,
            'last_purchase_time': self.last_purchase_time.isoformat() if self.last_purchase_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }