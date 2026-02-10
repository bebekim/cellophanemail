"""Tests for authentication endpoints."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from litestar import Litestar
from litestar.testing import TestClient

from cellophanemail.routes.auth import AuthController


@pytest.fixture
def test_client():
    """Create test client with AuthController only (no env vars needed)."""
    app = Litestar(route_handlers=[AuthController])
    return TestClient(app=app)


class TestUserRegistration:
    """Test user registration endpoint."""

    def test_register_user_success(self, test_client):
        """Test successful user registration."""
        with patch('cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=True)):
            with patch('cellophanemail.routes.auth.create_user', new=AsyncMock()) as mock_create:
                # Mock user object
                mock_user = MagicMock()
                mock_user.id = "test-uuid"
                mock_user.email = "test@example.com"
                mock_user.username = "test123"
                mock_user.first_name = "Test"
                mock_user.last_name = "User"
                mock_user.is_verified = False
                mock_user.verification_token = "test-token"
                mock_user.save = AsyncMock()
                mock_create.return_value = mock_user

                # Mock Stripe service
                with patch('cellophanemail.routes.auth.StripeService') as mock_stripe_class:
                    mock_stripe = mock_stripe_class.return_value
                    mock_customer = MagicMock()
                    mock_customer.id = "cus_test123"
                    mock_stripe.create_customer = AsyncMock(return_value=mock_customer)

                    # Mock create_auth_response
                    with patch('cellophanemail.routes.auth.create_auth_response', new=AsyncMock()) as mock_auth:
                        mock_auth.return_value = {
                            "access_token": "mock_token",
                            "refresh_token": "mock_refresh",
                            "token_type": "Bearer",
                            "expires_in": 900,
                            "user": {
                                "id": "test-uuid",
                                "email": "test@example.com",
                                "username": "test123",
                                "role": "user",
                                "is_verified": False
                            }
                        }

                        response = test_client.post(
                            "/api/v1/auth/register",
                            json={
                                "email": "test@example.com",
                                "password": "TestPass123!",
                                "first_name": "Test",
                                "last_name": "User"
                            }
                        )

                        assert response.status_code == 201
                        data = response.json()
                        assert "access_token" in data
                        assert "refresh_token" in data
                        assert data["shield_address"].endswith("@cellophanemail.com")
                        assert data["message"] is not None

    def test_register_user_duplicate_email(self, test_client):
        """Test registration with duplicate email."""
        with patch('cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=False)):
            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "password": "TestPass123!",
                    "first_name": "Test",
                    "last_name": "User"
                }
            )

            assert response.status_code == 400
            data = response.json()
            assert data["error"] == "Email already registered"
            assert data["field"] == "email"

    def test_register_user_weak_password(self, test_client):
        """Test registration with weak password."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",  # Too short, no uppercase, no digit
                "first_name": "Test",
                "last_name": "User"
            }
        )

        assert response.status_code == 400  # Validation error

    def test_register_user_invalid_email(self, test_client):
        """Test registration with invalid email format."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "TestPass123!",
                "first_name": "Test",
                "last_name": "User"
            }
        )

        assert response.status_code == 400  # Validation error
