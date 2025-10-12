"""Unit tests for StripeService.

Following TDD Red-Green-Refactor methodology.
Tests should mock all Stripe API calls to avoid real API usage.
"""

import pytest
import stripe
from unittest.mock import patch, MagicMock, AsyncMock
from cellophanemail.services.stripe_service import StripeService


class TestStripeServiceCreateCustomer:
    """Test StripeService.create_customer method."""

    @pytest.mark.asyncio
    async def test_create_customer_success(self):
        """Test successful customer creation with valid data."""
        # Arrange
        service = StripeService()
        user_id = "user-123"
        email = "test@example.com"
        name = "Test User"

        # Mock Stripe Customer.create
        with patch('stripe.Customer.create') as mock_create:
            mock_customer = MagicMock()
            mock_customer.id = "cus_123456789"
            mock_customer.email = email
            mock_customer.name = name
            mock_customer.metadata = {"user_id": user_id}
            mock_create.return_value = mock_customer

            # Act
            result = await service.create_customer(user_id, email, name)

            # Assert
            assert result.id == "cus_123456789"
            assert result.email == email
            assert result.name == name
            assert result.metadata["user_id"] == user_id
            mock_create.assert_called_once_with(
                email=email,
                name=name,
                metadata={"user_id": user_id}
            )

    @pytest.mark.asyncio
    async def test_create_customer_stripe_api_error(self):
        """Test customer creation when Stripe API fails."""
        # Arrange
        service = StripeService()
        user_id = "user-123"
        email = "test@example.com"
        name = "Test User"

        # Mock Stripe Customer.create to raise an error
        with patch('stripe.Customer.create') as mock_create:
            mock_create.side_effect = stripe.error.StripeError("API Error")

            # Act & Assert
            with pytest.raises(stripe.error.StripeError):
                await service.create_customer(user_id, email, name)


class TestStripeServiceCreateCheckoutSession:
    """Test StripeService.create_checkout_session method."""

    @pytest.mark.asyncio
    async def test_create_checkout_session_success(self):
        """Test successful checkout session creation."""
        # Arrange
        service = StripeService()
        customer_id = "cus_123456789"
        price_id = "price_123"
        success_url = "https://example.com/success"
        cancel_url = "https://example.com/cancel"
        trial_days = 30

        # Mock Stripe checkout.Session.create
        with patch('stripe.checkout.Session.create') as mock_create:
            mock_session = MagicMock()
            mock_session.id = "cs_test_123"
            mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
            mock_session.customer = customer_id
            mock_create.return_value = mock_session

            # Act
            result = await service.create_checkout_session(
                customer_id=customer_id,
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                trial_days=trial_days
            )

            # Assert
            assert result.id == "cs_test_123"
            assert result.url.startswith("https://checkout.stripe.com")
            assert result.customer == customer_id
            mock_create.assert_called_once_with(
                customer=customer_id,
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={"trial_period_days": trial_days},
                allow_promotion_codes=True
            )

    @pytest.mark.asyncio
    async def test_create_checkout_session_with_default_trial(self):
        """Test checkout session uses default 30-day trial."""
        # Arrange
        service = StripeService()

        with patch('stripe.checkout.Session.create') as mock_create:
            mock_session = MagicMock()
            mock_create.return_value = mock_session

            # Act
            await service.create_checkout_session(
                customer_id="cus_123",
                price_id="price_123",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel"
            )

            # Assert - verify trial_days defaults to 30
            call_args = mock_create.call_args[1]
            assert call_args["subscription_data"]["trial_period_days"] == 30


class TestStripeServiceCancelSubscription:
    """Test StripeService.cancel_subscription method."""

    @pytest.mark.asyncio
    async def test_cancel_subscription_at_period_end(self):
        """Test canceling subscription at period end."""
        # Arrange
        service = StripeService()
        subscription_id = "sub_123"

        with patch('stripe.Subscription.modify') as mock_modify:
            mock_subscription = MagicMock()
            mock_subscription.id = subscription_id
            mock_subscription.cancel_at_period_end = True
            mock_modify.return_value = mock_subscription

            # Act
            result = await service.cancel_subscription(subscription_id, at_period_end=True)

            # Assert
            assert result.cancel_at_period_end is True
            mock_modify.assert_called_once_with(
                subscription_id,
                cancel_at_period_end=True
            )

    @pytest.mark.asyncio
    async def test_cancel_subscription_immediately(self):
        """Test canceling subscription immediately."""
        # Arrange
        service = StripeService()
        subscription_id = "sub_123"

        with patch('stripe.Subscription.modify') as mock_modify:
            mock_subscription = MagicMock()
            mock_subscription.id = subscription_id
            mock_subscription.cancel_at_period_end = False
            mock_modify.return_value = mock_subscription

            # Act
            result = await service.cancel_subscription(subscription_id, at_period_end=False)

            # Assert
            assert result.cancel_at_period_end is False
            mock_modify.assert_called_once_with(
                subscription_id,
                cancel_at_period_end=False
            )


class TestStripeServiceCreatePortalSession:
    """Test StripeService.create_portal_session method."""

    @pytest.mark.asyncio
    async def test_create_portal_session_success(self):
        """Test successful portal session creation."""
        # Arrange
        service = StripeService()
        customer_id = "cus_123"
        return_url = "https://example.com/dashboard"

        with patch('stripe.billing_portal.Session.create') as mock_create:
            mock_session = MagicMock()
            mock_session.id = "bps_123"
            mock_session.url = "https://billing.stripe.com/session/bps_123"
            mock_create.return_value = mock_session

            # Act
            result = await service.create_portal_session(customer_id, return_url)

            # Assert
            assert result.id == "bps_123"
            assert result.url.startswith("https://billing.stripe.com")
            mock_create.assert_called_once_with(
                customer=customer_id,
                return_url=return_url
            )


class TestStripeServiceWebhookVerification:
    """Test StripeService.verify_webhook_signature method."""

    def test_verify_webhook_signature_success(self):
        """Test successful webhook signature verification."""
        # Arrange
        service = StripeService()
        payload = b'{"type": "customer.subscription.created"}'
        sig_header = "t=1614556800,v1=test_signature"

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_event = {
                "type": "customer.subscription.created",
                "data": {"object": {"id": "sub_123"}}
            }
            mock_construct.return_value = mock_event

            # Act
            result = service.verify_webhook_signature(payload, sig_header)

            # Assert
            assert result["type"] == "customer.subscription.created"
            mock_construct.assert_called_once_with(
                payload,
                sig_header,
                service.webhook_secret
            )

    def test_verify_webhook_signature_invalid(self):
        """Test webhook signature verification with invalid signature."""
        # Arrange
        service = StripeService()
        payload = b'{"type": "customer.subscription.created"}'
        sig_header = "invalid_signature"

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", sig_header
            )

            # Act & Assert
            with pytest.raises(stripe.error.SignatureVerificationError):
                service.verify_webhook_signature(payload, sig_header)
