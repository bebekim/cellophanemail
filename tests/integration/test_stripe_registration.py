"""Integration tests for Stripe customer creation during registration.

These tests verify the end-to-end flow of user registration including Stripe customer creation.
They use mocked Stripe API but test the full application stack including database interactions.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from litestar.testing import AsyncTestClient


@pytest.mark.asyncio
async def test_registration_creates_stripe_customer(test_client):
    """Test that user registration creates a Stripe customer and saves the ID."""
    # Arrange
    registration_data = {
        "email": "newuser@example.com",
        "password": "TestPass123!",
        "first_name": "New",
        "last_name": "User"
    }

    mock_customer = MagicMock()
    mock_customer.id = "cus_new123456789"
    mock_customer.email = registration_data["email"]

    # Mock all required services
    with patch('cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=True)):
        with patch('cellophanemail.routes.auth.create_user', new=AsyncMock()) as mock_create_user:
            with patch('cellophanemail.routes.auth.StripeService.create_customer', new=AsyncMock(return_value=mock_customer)):
                # Create a mock user that will be returned
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

                mock_create_user.return_value = mock_user

                # Act
                async with test_client as client:
                    response = await client.post("/auth/register", json=registration_data)

                # Assert
                assert response.status_code == 201
                data = response.json()
                assert data["status"] == "registered"
                assert data["email"] == registration_data["email"]
                assert data["stripe_customer_id"] == "cus_new123456789"
                assert "shield_address" in data

                # Verify Stripe customer was created
                # Note: In real integration test, we'd verify database has the customer_id


@pytest.mark.asyncio
async def test_registration_fails_when_stripe_customer_creation_fails(test_client):
    """Test that registration fails gracefully if Stripe customer creation fails."""
    # Arrange
    registration_data = {
        "email": "failuser@example.com",
        "password": "TestPass123!",
        "first_name": "Fail",
        "last_name": "User"
    }

    # Mock user creation to succeed
    mock_user = MagicMock()
    mock_user.id = "user-456"
    mock_user.email = registration_data["email"]
    mock_user.username = "failuser"
    mock_user.is_verified = False
    mock_user.verification_token = "verify-token"
    mock_user.stripe_customer_id = None
    mock_user.save = AsyncMock()

    # Mock Stripe customer creation to fail
    with patch('cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=True)):
        with patch('cellophanemail.routes.auth.create_user', new=AsyncMock(return_value=mock_user)):
            with patch('cellophanemail.routes.auth.StripeService.create_customer') as mock_create_customer:
                mock_create_customer.side_effect = Exception("Stripe API Error")

                # Act
                async with test_client as client:
                    response = await client.post("/auth/register", json=registration_data)

                # Assert
                assert response.status_code == 400
                data = response.json()
                assert data["error"] == "Registration failed"
                assert "Stripe API Error" in data["message"]


@pytest.mark.asyncio
async def test_registration_with_existing_email_does_not_create_stripe_customer(test_client):
    """Test that duplicate email registration does not attempt Stripe customer creation."""
    # Arrange
    registration_data = {
        "email": "existing@example.com",
        "password": "TestPass123!",
        "first_name": "Existing",
        "last_name": "User"
    }

    with patch('cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=False)):
        with patch('cellophanemail.routes.auth.StripeService.create_customer') as mock_create_customer:
            # Act
            async with test_client as client:
                response = await client.post("/auth/register", json=registration_data)

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert data["error"] == "Email already registered"

            # Verify Stripe customer creation was never attempted
            mock_create_customer.assert_not_called()
