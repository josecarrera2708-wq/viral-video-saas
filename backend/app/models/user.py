"""
User model
"""

from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime
from uuid import uuid4
from ..database import Base


class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)

    # Subscription
    subscription_tier = Column(String, default="free")  # free, creator, pro, business
    credits_balance = Column(Integer, default=0)
    stripe_customer_id = Column(String, nullable=True)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.email}>"
