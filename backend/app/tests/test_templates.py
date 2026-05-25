"""
Templates endpoint tests
"""

import pytest


def test_list_templates(client):
    """Test listing all templates"""
    response = client.get("/api/v1/templates")
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert "total" in data
    assert "categories" in data
    assert len(data["templates"]) > 0
    assert data["total"] > 0


def test_list_templates_with_category_filter(client):
    """Test listing templates filtered by category"""
    response = client.get("/api/v1/templates?category=business")
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert all(t["category"] == "business" for t in data["templates"])


def test_list_templates_trending_only(client):
    """Test listing only trending templates"""
    response = client.get("/api/v1/templates?trending_only=true")
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert all(t["is_trending"] for t in data["templates"])


def test_get_single_template(client):
    """Test getting a specific template"""
    # First get all templates
    list_response = client.get("/api/v1/templates")
    assert list_response.status_code == 200
    templates = list_response.json()["templates"]
    assert len(templates) > 0

    # Then get specific template
    template_id = templates[0]["id"]
    response = client.get(f"/api/v1/templates/{template_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert "name" in data
    assert "category" in data
    assert "kling_style_id" in data


def test_get_nonexistent_template(client):
    """Test getting non-existent template"""
    response = client.get("/api/v1/templates/nonexistent")
    assert response.status_code == 404
