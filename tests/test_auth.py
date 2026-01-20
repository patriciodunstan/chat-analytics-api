"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["role"] == "viewer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Test registration with existing email fails."""
    response = await client.post(
        "/auth/register",
        json={
            "email": test_user.email,
            "password": "anotherpass",
            "full_name": "Another User",
        },
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login."""
    response = await client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "testpass123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == test_user.email


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password fails."""
    response = await client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword",
        },
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers, test_user):
    """Test getting current user."""
    response = await client.get("/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test getting current user without auth fails."""
    response = await client.get("/auth/me")

    assert response.status_code == 401  # No bearer token (FastAPI default)
