"""
Stripe Payment Integration
Handle checkout sessions and credit purchases
"""

import stripe
from typing import Dict, Any, Optional
import logging
from ..config import settings

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service for Stripe payment operations"""

    @staticmethod
    def create_checkout_session(
        user_id: str,
        user_email: str,
        package_id: str,
        success_url: str,
        cancel_url: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Create Stripe checkout session for credit purchase

        Args:
            user_id: User ID for metadata
            user_email: User email
            package_id: Credit package (basic, pro, business)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            {"session_id": str, "url": str}
        """

        # Package details
        packages = {
            "basic": {"credits": 50, "price_usd": 9.99},
            "pro": {"credits": 125, "price_usd": 19.99},
            "business": {"credits": 400, "price_usd": 49.99},
        }

        if package_id not in packages:
            logger.error(f"Invalid package: {package_id}")
            return None

        package = packages[package_id]

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"Video Credits - {package_id.title()}",
                                "description": f"{package['credits']} credits for video generation",
                                "images": ["https://viral-video.app/logo.png"],
                            },
                            "unit_amount": int(package["price_usd"] * 100),
                        },
                        "quantity": 1,
                    }
                ],
                customer_email=user_email,
                metadata={
                    "user_id": user_id,
                    "package_id": package_id,
                    "credits": package["credits"],
                },
                success_url=success_url,
                cancel_url=cancel_url,
                mode="payment",
            )

            logger.info(f"Checkout session created: {session.id}")

            return {
                "session_id": session.id,
                "url": session.url,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return None

    @staticmethod
    def retrieve_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve checkout session details"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "id": session.id,
                "status": session.payment_status,
                "customer_email": session.customer_email,
                "metadata": session.metadata,
                "amount_total": session.amount_total,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve session: {e}")
            return None

    @staticmethod
    def verify_webhook(payload: bytes, sig_header: str, webhook_secret: str) -> Optional[Dict[str, Any]]:
        """
        Verify Stripe webhook signature and return event

        Args:
            payload: Raw webhook body
            sig_header: Stripe signature header
            webhook_secret: Webhook signing secret

        Returns:
            Event dict or None if verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                webhook_secret,
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return None

    @staticmethod
    def get_credit_packages() -> list[Dict[str, Any]]:
        """Get available credit packages"""
        return [
            {
                "id": "basic",
                "name": "Basic",
                "credits": 50,
                "price_usd": 9.99,
                "price_per_credit": 0.20,
            },
            {
                "id": "pro",
                "name": "Professional",
                "credits": 125,
                "price_usd": 19.99,
                "price_per_credit": 0.16,
            },
            {
                "id": "business",
                "name": "Business",
                "credits": 400,
                "price_usd": 49.99,
                "price_per_credit": 0.12,
            },
        ]

    @staticmethod
    def create_customer(user_id: str, user_email: str) -> Optional[str]:
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=user_email,
                metadata={"user_id": user_id},
            )
            logger.info(f"Stripe customer created: {customer.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer: {e}")
            return None
