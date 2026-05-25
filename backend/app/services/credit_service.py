"""
Credit System Service
Manages user credits, billing, and transactions
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
import logging
from ..config import settings
from ..models.user import User
from ..models.credit_transaction import CreditTransaction

logger = logging.getLogger(__name__)


class CreditService:
    """Service for managing credits and billing"""

    @staticmethod
    def calculate_video_cost(duration_seconds: int) -> int:
        """
        Calculate credits needed for a video

        Formula: overhead + (duration * per_second_rate)
        Example: 30s video = 30 + (30 * 0.07) = 32.1 credits

        Args:
            duration_seconds: Video duration in seconds

        Returns:
            Credits required (integer)
        """
        overhead = settings.video_credit_overhead  # 30
        per_second = settings.video_credit_cost_per_sec  # 0.07
        total = overhead + (duration_seconds * per_second)
        return int(total)

    @staticmethod
    def get_user_credits(user_id: str, db: Session) -> int:
        """Get current credit balance for user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        return user.credits_balance

    @staticmethod
    def debit_credits(
        user_id: str,
        amount: int,
        reason: str,
        video_id: str = None,
        db: Session = None,
    ) -> tuple[bool, str]:
        """
        Debit credits from user account

        Returns:
            (success: bool, message: str)
        """
        if db is None:
            return False, "Database session required"

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found"

            if user.credits_balance < amount:
                return False, f"Insufficient credits (have {user.credits_balance}, need {amount})"

            # Debit credits
            user.credits_balance -= amount

            # Log transaction
            transaction = CreditTransaction(
                user_id=user_id,
                amount=-amount,  # Negative for debit
                type="debit",
                reason=reason,
                video_id=video_id,
            )
            db.add(transaction)
            db.commit()

            logger.info(f"Credited {amount} from user {user_id} for {reason}")
            return True, "Credits debited successfully"

        except Exception as e:
            db.rollback()
            logger.error(f"Credit debit error: {e}")
            return False, str(e)

    @staticmethod
    def credit_user(
        user_id: str,
        amount: int,
        reason: str,
        db: Session = None,
    ) -> tuple[bool, str]:
        """
        Add credits to user account

        Returns:
            (success: bool, message: str)
        """
        if db is None:
            return False, "Database session required"

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found"

            # Add credits
            user.credits_balance += amount

            # Log transaction
            transaction = CreditTransaction(
                user_id=user_id,
                amount=amount,
                type="credit",
                reason=reason,
            )
            db.add(transaction)
            db.commit()

            logger.info(f"Credited {amount} to user {user_id} for {reason}")
            return True, "Credits added successfully"

        except Exception as e:
            db.rollback()
            logger.error(f"Credit add error: {e}")
            return False, str(e)

    @staticmethod
    def refund_video(
        user_id: str,
        video_id: str,
        original_cost: int,
        db: Session = None,
    ) -> tuple[bool, str]:
        """
        Refund credits for a failed/deleted video

        Returns:
            (success: bool, message: str)
        """
        if db is None:
            return False, "Database session required"

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found"

            # Add credits back
            user.credits_balance += original_cost

            # Log transaction
            transaction = CreditTransaction(
                user_id=user_id,
                amount=original_cost,
                type="refund",
                reason="video_deleted_or_failed",
                video_id=video_id,
            )
            db.add(transaction)
            db.commit()

            logger.info(f"Refunded {original_cost} credits to user {user_id} for video {video_id}")
            return True, "Refund processed successfully"

        except Exception as e:
            db.rollback()
            logger.error(f"Refund error: {e}")
            return False, str(e)

    @staticmethod
    def get_transaction_history(
        user_id: str,
        limit: int = 50,
        db: Session = None,
    ) -> list:
        """Get user's credit transaction history"""
        if db is None:
            return []

        transactions = (
            db.query(CreditTransaction)
            .filter(CreditTransaction.user_id == user_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "reason": t.reason,
                "created_at": t.created_at,
            }
            for t in transactions
        ]

    @staticmethod
    def get_credit_packages() -> list[dict]:
        """
        Get available credit packages for purchase

        Returns:
            List of purchase options
        """
        return [
            {
                "id": "basic",
                "credits": 50,
                "price_usd": 9.99,
                "price_per_credit": 0.20,
                "popular": False,
            },
            {
                "id": "pro",
                "credits": 125,
                "price_usd": 19.99,
                "price_per_credit": 0.16,
                "popular": True,
            },
            {
                "id": "business",
                "credits": 400,
                "price_usd": 49.99,
                "price_per_credit": 0.12,
                "popular": False,
            },
        ]
