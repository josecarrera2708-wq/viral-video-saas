"""
User API routes
GET /api/v1/user - get current user profile
PATCH /api/v1/user - update user settings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.credit_transaction import CreditTransaction

router = APIRouter(prefix="/api/v1", tags=["user"])


class UserResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    name: str
    subscription_tier: str
    credits_balance: int
    videos_created: int
    created_at: datetime
    stripe_customer_id: str = None

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Update user profile request"""
    name: str = None
    email: str = None


class TransactionResponse(BaseModel):
    """Credit transaction response"""
    id: str
    user_id: str
    amount: int
    type: str  # debit, credit, refund, promo
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/user")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile with credits balance

    Returns:
    - id, email, name, subscription_tier, credits_balance
    - videos_created count
    - created_at timestamp
    """
    # Count user's videos
    from ..models.video import Video
    video_count = db.query(Video).filter(
        Video.user_id == current_user.id
    ).count()

    user_response = {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "subscription_tier": current_user.subscription_tier,
        "credits_balance": current_user.credits_balance,
        "videos_created": video_count,
        "created_at": current_user.created_at,
        "stripe_customer_id": current_user.stripe_customer_id
    }

    return user_response


@router.patch("/user")
async def update_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile

    Allowed fields:
    - name: User display name
    - email: Email address (must be unique)

    Returns:
    - Updated user profile
    """
    if update_data.name:
        current_user.name = update_data.name

    if update_data.email:
        # Check if email is already taken
        existing = db.query(User).filter(
            User.email == update_data.email,
            User.id != current_user.id
        ).first()

        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")

        current_user.email = update_data.email

    db.commit()
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "subscription_tier": current_user.subscription_tier,
        "credits_balance": current_user.credits_balance,
        "message": "Profile updated successfully"
    }


@router.get("/user/transactions")
async def get_transaction_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get credit transaction history for current user

    Query parameters:
    - limit: Number of transactions (default 50, max 100)
    - offset: Pagination offset (default 0)

    Returns:
    - List of credit transactions sorted by newest first
    """
    limit = min(limit, 100)  # Cap at 100

    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.user_id == current_user.id
    ).order_by(
        CreditTransaction.created_at.desc()
    ).limit(limit).offset(offset).all()

    total_count = db.query(CreditTransaction).filter(
        CreditTransaction.user_id == current_user.id
    ).count()

    return {
        "transactions": [
            {
                "id": t.id,
                "user_id": t.user_id,
                "amount": t.amount,
                "type": t.type,
                "reason": t.reason,
                "created_at": t.created_at
            }
            for t in transactions
        ],
        "total": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/user/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics

    Returns:
    - Total videos created
    - Total videos this month
    - Videos by status (completed, failed, processing)
    - Credits spent this month
    """
    from ..models.video import Video
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Videos created
    all_videos = db.query(Video).filter(
        Video.user_id == current_user.id
    ).all()

    # Videos this month
    month_ago = datetime.utcnow() - timedelta(days=30)
    monthly_videos = db.query(Video).filter(
        Video.user_id == current_user.id,
        Video.created_at >= month_ago
    ).all()

    # Videos by status
    statuses = {}
    for video in all_videos:
        status = video.state
        statuses[status] = statuses.get(status, 0) + 1

    # Credits spent this month
    monthly_debits = db.query(func.sum(CreditTransaction.amount)).filter(
        CreditTransaction.user_id == current_user.id,
        CreditTransaction.type == "debit",
        CreditTransaction.created_at >= month_ago
    ).scalar() or 0

    return {
        "total_videos": len(all_videos),
        "videos_this_month": len(monthly_videos),
        "videos_by_status": statuses,
        "credits_spent_this_month": abs(monthly_debits),
        "current_credits": current_user.credits_balance,
        "subscription_tier": current_user.subscription_tier
    }
