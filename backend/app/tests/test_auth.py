"""
Auth endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# These would be run with: pytest backend/tests/


def test_signup_success(client):
    """Test successful user signup"""
    response = client.post(
        "/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "name": "New User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "newuser@example.com"
    assert data["user"]["subscription_tier"] == "free"
    assert data["user"]["credits_balance"] == 0


def test_signup_duplicate_email(client, db_user):
    """Test signup with existing email"""
    response = client.post(
        "/auth/signup",
        json={
            "email": db_user.email,
            "password": "password123",
            "name": "Duplicate User",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client, db_user):
    """Test successful login"""
    response = client.post(
        "/auth/login",
        json={
            "email": db_user.email,
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == db_user.email


def test_login_invalid_password(client, db_user):
    """Test login with wrong password"""
    response = client.post(
        "/auth/login",
        json={
            "email": db_user.email,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


def test_get_current_user(client, token):
    """Test getting current user profile"""
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "credits_balance" in data


def test_get_current_user_no_token(client):
    """Test getting current user without token"""
    response = client.get("/auth/me")
    assert response.status_code == 401
