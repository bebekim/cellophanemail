"""Tests for billing routes."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from litestar import Litestar
from litestar.testing import AsyncTestClient

from cellophanemail.routes.billing import BillingController
from cellophanemail.middleware.jwt_auth import JWTAuthenticationMiddleware, JWTUser
from tests.factories import UserFactory, StripeFactory, JWTFactory


def _create_billing_app():
    """Create a minimal Litestar app with the BillingController for testing."""
    return Litestar(
        route_handlers=[BillingController],
        middleware=[JWTAuthenticationMiddleware],
    )


class TestCreateCheckoutRoute:
    """Test /billing/create-checkout endpoint."""

    @pytest.mark.asyncio
    async def test_create_checkout_authenticated_user(self):
        """Test creating checkout session with authenticated user."""
        token = JWTFactory.create_access_token(
            user_id="user-123",
            email="test@example.com"
        )

        mock_session = StripeFactory.create_checkout_session(
            session_id="cs_test_123",
            url="https://checkout.stripe.com/session/123"
        )

        # Patch JWTUser.from_token_payload to return a mock with DB fields
        mock_user = MagicMock(spec=JWTUser)
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.role = "user"
        mock_user.is_authenticated = True
        mock_user.stripe_customer_id = "cus_existing_123"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.save = AsyncMock()

        with patch.object(JWTUser, 'from_token_payload', new=AsyncMock(return_value=mock_user)):
            with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
                mock_service = MagicMock()
                mock_service.create_checkout_session = AsyncMock(return_value=mock_session)
                MockStripeService.return_value = mock_service

                app = _create_billing_app()
                async with AsyncTestClient(app=app) as client:
                    response = await client.post(
                        "/billing/create-checkout",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"price_id": "price_test_123"}
                    )

        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert data["checkout_url"] == "https://checkout.stripe.com/session/123"

    @pytest.mark.asyncio
    async def test_create_checkout_unauthenticated(self):
        """Test that checkout requires authentication."""
        app = _create_billing_app()
        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/billing/create-checkout",
                json={"price_id": "price_test_123"}
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_checkout_missing_price_id(self):
        """Test checkout with missing price_id."""
        token = JWTFactory.create_access_token()

        mock_user = MagicMock(spec=JWTUser)
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.role = "user"
        mock_user.is_authenticated = True
        mock_user.stripe_customer_id = "cus_123"
        mock_user.save = AsyncMock()

        with patch.object(JWTUser, 'from_token_payload', new=AsyncMock(return_value=mock_user)):
            app = _create_billing_app()
            async with AsyncTestClient(app=app) as client:
                response = await client.post(
                    "/billing/create-checkout",
                    headers={"Authorization": f"Bearer {token}"},
                    json={}
                )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_checkout_stripe_error(self):
        """Test checkout when Stripe API fails."""
        token = JWTFactory.create_access_token()

        mock_user = MagicMock(spec=JWTUser)
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.role = "user"
        mock_user.is_authenticated = True
        mock_user.stripe_customer_id = "cus_123"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.save = AsyncMock()

        with patch.object(JWTUser, 'from_token_payload', new=AsyncMock(return_value=mock_user)):
            with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
                mock_service = MagicMock()
                mock_service.create_checkout_session = AsyncMock(
                    side_effect=Exception("Stripe API error")
                )
                MockStripeService.return_value = mock_service

                app = _create_billing_app()
                async with AsyncTestClient(app=app) as client:
                    response = await client.post(
                        "/billing/create-checkout",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"price_id": "price_test_123"}
                    )

        assert response.status_code == 500


class TestCustomerPortalRoute:
    """Test /billing/portal endpoint."""

    @pytest.mark.asyncio
    async def test_customer_portal_authenticated_user(self):
        """Test creating customer portal session."""
        token = JWTFactory.create_access_token(user_id="user-123")

        mock_session = StripeFactory.create_portal_session(
            session_id="bps_test_123",
            url="https://billing.stripe.com/session/123"
        )

        mock_user = MagicMock(spec=JWTUser)
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.role = "user"
        mock_user.is_authenticated = True
        mock_user.stripe_customer_id = "cus_123"

        with patch.object(JWTUser, 'from_token_payload', new=AsyncMock(return_value=mock_user)):
            with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
                mock_service = MagicMock()
                mock_service.create_portal_session = AsyncMock(return_value=mock_session)
                MockStripeService.return_value = mock_service

                app = _create_billing_app()
                async with AsyncTestClient(app=app) as client:
                    response = await client.get(
                        "/billing/portal",
                        headers={"Authorization": f"Bearer {token}"},
                        follow_redirects=False,
                    )

        assert response.status_code == 303
        assert response.headers["location"] == "https://billing.stripe.com/session/123"

    @pytest.mark.asyncio
    async def test_customer_portal_unauthenticated(self):
        """Test that portal requires authentication."""
        app = _create_billing_app()
        async with AsyncTestClient(app=app) as client:
            response = await client.get("/billing/portal")

        assert response.status_code == 401
