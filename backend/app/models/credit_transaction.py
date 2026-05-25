"""
Credit transaction model
Audit log for credit ledger
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from uuid import uuid4
from ..database import Base


class CreditTransaction(Base):
    """Credit transaction audit log"""
    __tablename__ = "credit_transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Transaction
    amount = Column(Integer, nullable=False)  # Can be negative for debits
    type = Column(String, nullable=False)  # debit, credit, refund, promo
    reason = Column(String, nullable=False)  # "video_generation", "purchase", "refund", etc
    video_id = Column(String, nullable=True)  # Link to video if applicable

    # Metadata
    created_at = Column(DateTime, server_default=func.now(), index=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<CreditTransaction {self.type} {self.amount} for user {self.user_id}>"
