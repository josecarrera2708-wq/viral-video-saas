"""
Payment Routes
Stripe checkout and webhook handling
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from ..database import get_db
from ..models.user import User
from ..auth import verify_token
from ..services.stripe_service import StripeService
from ..services.credit_service import CreditService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


class CheckoutRequest(BaseModel):
    """Checkout session request"""
    package_id: str  # basic, pro, business


class CheckoutResponse(BaseModel):
    """Checkout response"""
    session_id: str
    url: str


async def get_current_user(
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Extract and verify JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )

        token = parts[1]
        token_data = verify_token(token)

        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.get("/packages")
async def get_packages():
    """Get available credit packages"""
    packages = StripeService.get_credit_packages()
    return {"packages": packages}


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create Stripe checkout session for credit purchase

    Returns session ID and URL to redirect user
    """

    user = await get_current_user(authorization, db)

    # Validate package
    valid_packages = ["basic", "pro", "business"]
    if request.package_id not in valid_packages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid package. Must be one of: {valid_packages}"
        )

    # Create checkout session
    success_url = "http://localhost:3000/account/billing?success=true"
    cancel_url = "http://localhost:3000/account/billing?canceled=true"

    session_data = StripeService.create_checkout_session(
        user_id=user.id,
        user_email=user.email,
        package_id=request.package_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

    return CheckoutResponse(
        session_id=session_data["session_id"],
        url=session_data["url"],
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Stripe webhook handler for payment completion
    Adds credits to user account when payment succeeds
    """

    from ..config import settings

    # Get webhook secret
    webhook_secret = "whsec_test_secret"  # In production: settings.STRIPE_WEBHOOK_SECRET

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        logger.warning("Webhook missing signature header")
        return {"status": "ignored"}

    # Verify webhook
    event = StripeService.verify_webhook(payload, sig_header, webhook_secret)
    if not event:
        raise HTTPException(status_code=400, detail="Invalid signature")

    logger.info(f"Webhook event: {event['type']}")

    # Handle checkout.session.completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Get metadata
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        package_id = metadata.get("package_id")
        credits = int(metadata.get("credits", 0))

        if not user_id or not credits:
            logger.error("Missing metadata in webhook")
            return {"status": "error"}

        # Update user credits
        success, msg = CreditService.credit_user(
            user_id=user_id,
            amount=credits,
            reason=f"stripe_payment_{package_id}",
            db=db,
        )

        if success:
            logger.info(f"Credits added: {user_id} +{credits}")
            return {"status": "success"}
        else:
            logger.error(f"Failed to add credits: {msg}")
            return {"status": "error"}

    return {"status": "ignored"}


@router.get("/transactions")
async def get_transactions(
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get user's payment transaction history"""

    user = await get_current_user(authorization, db)

    transactions = CreditService.get_transaction_history(
        user_id=user.id,
        limit=100,
        db=db,
    )

    return {"transactions": transactions}
