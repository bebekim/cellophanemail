"""Tests for billing routes."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from tests.factories import UserFactory, StripeFactory, JWTFactory
from tests.assertions import assert_http_error_response


@pytest.mark.asyncio
class TestCreateCheckoutRoute:
    """Test /billing/create-checkout endpoint."""

    async def test_create_checkout_authenticated_user(self, test_client):
        """Test creating checkout session with authenticated user."""
        # Create real JWT token
        token = JWTFactory.create_access_token(
            user_id="user-123",
            email="test@example.com"
        )

        # Mock Stripe service
        mock_session = StripeFactory.create_checkout_session(
            session_id="cs_test_123",
            url="https://checkout.stripe.com/session/123"
        )

        with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
            mock_service = MagicMock()
            mock_service.create_checkout_session = AsyncMock(return_value=mock_session)
            MockStripeService.return_value = mock_service

            # Make authenticated request
            response = await test_client.post(
                "/billing/create-checkout",
                headers={"Authorization": f"Bearer {token}"},
                json={"price_id": "price_test_123"}
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert data["checkout_url"] == "https://checkout.stripe.com/session/123"
        assert "session_id" in data
        assert data["session_id"] == "cs_test_123"

    async def test_create_checkout_unauthenticated(self, test_client):
        """Test that checkout requires authentication."""
        # No auth token
        response = await test_client.post(
            "/billing/create-checkout",
            json={"price_id": "price_test_123"}
        )

        # Should be unauthorized
        assert response.status_code == 401

    async def test_create_checkout_missing_price_id(self, test_client):
        """Test checkout with missing price_id."""
        token = JWTFactory.create_access_token()

        # No price_id in request
        response = await test_client.post(
            "/billing/create-checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={}
        )

        # Should be bad request
        assert response.status_code == 400

    async def test_create_checkout_stripe_error(self, test_client):
        """Test checkout when Stripe API fails."""
        token = JWTFactory.create_access_token()

        with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
            mock_service = MagicMock()
            mock_service.create_checkout_session = AsyncMock(
                side_effect=Exception("Stripe API error")
            )
            MockStripeService.return_value = mock_service

            response = await test_client.post(
                "/billing/create-checkout",
                headers={"Authorization": f"Bearer {token}"},
                json={"price_id": "price_test_123"}
            )

        # Should return error
        assert response.status_code == 500
        assert_http_error_response(response, 500, "error")


@pytest.mark.asyncio
class TestCustomerPortalRoute:
    """Test /billing/customer-portal endpoint."""

    async def test_customer_portal_authenticated_user(self, test_client):
        """Test creating customer portal session."""
        token = JWTFactory.create_access_token(user_id="user-123")

        # Mock Stripe service
        mock_session = StripeFactory.create_portal_session(
            session_id="bps_test_123",
            url="https://billing.stripe.com/session/123"
        )

        with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
            mock_service = MagicMock()
            mock_service.create_portal_session = AsyncMock(return_value=mock_session)
            MockStripeService.return_value = mock_service

            response = await test_client.post(
                "/billing/customer-portal",
                headers={"Authorization": f"Bearer {token}"}
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "portal_url" in data
        assert data["portal_url"] == "https://billing.stripe.com/session/123"

    async def test_customer_portal_unauthenticated(self, test_client):
        """Test that portal requires authentication."""
        response = await test_client.post("/billing/customer-portal")

        assert response.status_code == 401

    async def test_customer_portal_user_without_customer_id(self, test_client):
        """Test portal for user without Stripe customer ID."""
        token = JWTFactory.create_access_token(user_id="user-no-stripe")

        with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
            mock_service = MagicMock()
            # Mock get_user to return user without stripe_customer_id
            with patch('cellophanemail.routes.billing.User') as MockUser:
                mock_user_query = MagicMock()
                mock_user = UserFactory.create_user(stripe_customer_id=None)
                mock_user_query.first = AsyncMock(return_value=mock_user)
                MockUser.objects.return_value.where.return_value = mock_user_query

                response = await test_client.post(
                    "/billing/customer-portal",
                    headers={"Authorization": f"Bearer {token}"}
                )

        # Should return error
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
