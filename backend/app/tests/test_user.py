"""
User endpoint tests
"""

import pytest


def test_get_user_profile(client, token):
    """Test getting current user profile"""
    response = client.get(
        "/api/v1/user",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "name" in data
    assert "credits_balance" in data
    assert "subscription_tier" in data
    assert "videos_created" in data
    assert data["subscription_tier"] == "free"
    assert data["credits_balance"] == 0


def test_get_user_profile_no_auth(client):
    """Test getting user profile without authentication"""
    response = client.get("/api/v1/user")
    assert response.status_code == 403


def test_update_user_name(client, token, db_user):
    """Test updating user name"""
    response = client.patch(
        "/api/v1/user",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_update_user_email_unique(client, token):
    """Test updating user email with unique email"""
    response = client.patch(
        "/api/v1/user",
        json={"email": "newemail@example.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "newemail@example.com"


def test_update_user_email_duplicate(client, token, db):
    """Test updating user email with duplicate email"""
    # Create another user
    from ..models.user import User
    from ..auth import get_password_hash

    other_user = User(
        email="other@example.com",
        name="Other User",
        hashed_password=get_password_hash("pass123"),
        subscription_tier="free",
        credits_balance=0
    )
    db.add(other_user)
    db.commit()

    response = client.patch(
        "/api/v1/user",
        json={"email": "other@example.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 409


def test_get_transaction_history(client, token, db, db_user):
    """Test getting credit transaction history"""
    from ..models.credit_transaction import CreditTransaction

    # Add test transactions
    for i in range(3):
        transaction = CreditTransaction(
            user_id=db_user.id,
            amount=-50 if i % 2 == 0 else 100,
            type="debit" if i % 2 == 0 else "credit",
            reason=f"Test transaction {i}"
        )
        db.add(transaction)
    db.commit()

    response = client.get(
        "/api/v1/user/transactions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
    assert data["total"] == 3
    assert len(data["transactions"]) == 3


def test_get_user_stats(client, token, db, db_user):
    """Test getting user statistics"""
    response = client.get(
        "/api/v1/user/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_videos" in data
    assert "videos_this_month" in data
    assert "videos_by_status" in data
    assert "credits_spent_this_month" in data
    assert "current_credits" in data
    assert "subscription_tier" in data
