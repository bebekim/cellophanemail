"""Integration tests for Stripe customer creation during registration.

These tests verify the end-to-end flow of user registration including Stripe customer creation.
They use mocked Stripe API but test the full application stack including database interactions.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_registration_creates_stripe_customer(test_client):
    """Test that user registration creates a Stripe customer and saves the ID."""
    registration_data = {
        "email": "newuser@example.com",
        "password": "TestPass123!",
        "first_name": "New",
        "last_name": "User"
    }

    mock_customer = MagicMock()
    mock_customer.id = "cus_new123456789"
    mock_customer.email = registration_data["email"]

    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = registration_data["email"]
    mock_user.username = "newuser"
    mock_user.is_verified = False
    mock_user.verification_token = "verify-token"
    mock_user.first_name = "New"
    mock_user.last_name = "User"
    mock_user.stripe_customer_id = None
    mock_user.save = AsyncMock()

    with patch('cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=True)):
        with patch('cellophanemail.routes.auth.create_user', new=AsyncMock(return_value=mock_user)):
            with patch('cellophanemail.routes.auth.StripeService') as MockStripe:
                mock_stripe_instance = MockStripe.return_value
                mock_stripe_instance.create_customer = AsyncMock(return_value=mock_customer)

                with patch('cellophanemail.routes.auth.create_auth_response', new=AsyncMock(return_value={
                    "access_token": "mock_token",
                    "refresh_token": "mock_refresh",
                    "token_type": "Bearer",
                    "expires_in": 900,
                    "user": {
                        "id": "user-123",
                        "email": registration_data["email"],
                        "username": "newuser",
                        "role": "user",
                        "is_verified": False
                    }
                })):
                    response = await test_client.post(
                        "/api/v1/auth/register", json=registration_data
                    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "shield_address" in data
    assert "@cellophanemail.com" in data["shield_address"]

    # Verify Stripe customer ID was stored on user
    assert mock_user.stripe_customer_id == "cus_new123456789"
    mock_user.save.assert_called_once()


@pytest.mark.asyncio
async def test_registration_fails_when_stripe_customer_creation_fails(test_client):
    """Test that registration fails gracefully if Stripe customer creation fails."""
    registration_data = {
        "email": "failuser@example.com",
        "password": "TestPass123!",
        "first_name": "Fail",
        "last_name": "User"
    }

    mock_user = MagicMock()
    mock_user.id = "user-456"
    mock_user.email = registration_data["email"]
    mock_user.username = "failuser"
    mock_user.is_verified = False
    mock_user.verification_token = "verify-token"
    mock_user.stripe_customer_id = None
    mock_user.save = AsyncMock()

    with patch('cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=True)):
        with patch('cellophanemail.routes.auth.create_user', new=AsyncMock(return_value=mock_user)):
            with patch('cellophanemail.routes.auth.StripeService') as MockStripe:
                mock_stripe_instance = MockStripe.return_value
                mock_stripe_instance.create_customer = AsyncMock(
                    side_effect=Exception("Stripe API Error")
                )

                response = await test_client.post(
                    "/api/v1/auth/register", json=registration_data
                )

    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "Registration failed"
    assert "Stripe API Error" in data["message"]


@pytest.mark.asyncio
async def test_registration_with_existing_email_does_not_create_stripe_customer(test_client):
    """Test that duplicate email registration does not attempt Stripe customer creation."""
    registration_data = {
        "email": "existing@example.com",
        "password": "TestPass123!",
        "first_name": "Existing",
        "last_name": "User"
    }

    with patch('cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=False)):
        with patch('cellophanemail.routes.auth.StripeService') as MockStripe:
            mock_stripe_instance = MockStripe.return_value
            mock_stripe_instance.create_customer = AsyncMock()

            response = await test_client.post(
                "/api/v1/auth/register", json=registration_data
            )

    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "Email already registered"

    # Verify Stripe customer creation was never attempted
    mock_stripe_instance.create_customer.assert_not_called()
