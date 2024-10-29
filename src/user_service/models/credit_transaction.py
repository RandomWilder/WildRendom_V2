from datetime import datetime, timezone
from src.shared import db

class CreditTransaction(db.Model):
    """Track all credit-related transactions"""
    __tablename__ = 'credit_transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'add', 'subtract', 'refund'
    balance_after = db.Column(db.Float, nullable=False)
    reference_type = db.Column(db.String(50))  # e.g., 'raffle_purchase', 'admin_adjustment', 'promotion'
    reference_id = db.Column(db.String(100))   # ID of the related entity (if any)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'balance_after': self.balance_after,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'created_by_id': self.created_by_id
        }