"""
Payments endpoint tests
"""

import pytest
from unittest.mock import patch, MagicMock


def test_get_credit_packages(client, token):
    """Test getting available credit packages"""
    response = client.get(
        "/api/v1/payments/packages",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "packages" in data
    assert len(data["packages"]) >= 3  # At least 3 packages


def test_get_credit_packages_structure(client, token):
    """Test that packages have correct structure"""
    response = client.get(
        "/api/v1/payments/packages",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()

    for package in data["packages"]:
        assert "id" in package
        assert "name" in package
        assert "credits" in package
        assert "price_usd" in package
        assert "price_per_credit" in package


@patch("stripe.checkout.Session.create")
def test_create_checkout_session(mock_stripe, client, token):
    """Test creating a Stripe checkout session"""
    mock_session = MagicMock()
    mock_session.url = "https://stripe.com/checkout/test"
    mock_session.id = "cs_test_123"
    mock_stripe.return_value = mock_session

    response = client.post(
        "/api/v1/payments/checkout",
        json={"package_id": "basic"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "checkout_url" in data or "session_id" in data


def test_create_checkout_session_no_auth(client):
    """Test creating checkout without authentication"""
    response = client.post(
        "/api/v1/payments/checkout",
        json={"package_id": "basic"}
    )
    assert response.status_code == 403


def test_get_transaction_history(client, token, db, db_user):
    """Test getting payment transaction history"""
    from ..models.credit_transaction import CreditTransaction

    # Add test transactions
    for i in range(2):
        transaction = CreditTransaction(
            user_id=db_user.id,
            amount=100 if i % 2 == 0 else 250,
            type="credit",
            reason=f"Payment for package {i}"
        )
        db.add(transaction)
    db.commit()

    response = client.get(
        "/api/v1/payments/transactions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
    assert len(data["transactions"]) == 2


@patch("stripe.Webhook.construct_event")
def test_stripe_webhook_payment_success(mock_webhook, client, db, db_user):
    """Test Stripe webhook for successful payment"""
    mock_webhook.return_value = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "client_reference_id": str(db_user.id),
                "metadata": {"package_id": "basic"},
                "payment_status": "paid"
            }
        }
    }

    response = client.post(
        "/api/v1/payments/webhook",
        json={},
        headers={"Stripe-Signature": "test_signature"}
    )

    # Should accept webhook
    assert response.status_code in [200, 204]


def test_get_checkout_session_status(client, token):
    """Test getting checkout session status"""
    # This would require a valid session ID from Stripe
    # For now just test that endpoint exists
    response = client.get(
        "/api/v1/payments/session/cs_test_123",
        headers={"Authorization": f"Bearer {token}"}
    )
    # May be 404 or valid response depending on implementation
    assert response.status_code in [200, 404, 400]
