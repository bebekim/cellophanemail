"""Unit tests for Stripe Webhook Handler.

Following TDD Red-Green-Refactor methodology.
Tests webhook event handling logic (private methods).
Integration tests will cover full HTTP endpoint behavior.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock, call
from cellophanemail.routes.stripe_webhooks import StripeWebhookHandler


class TestSubscriptionCreatedWebhook:
    """Test handling of subscription.created webhook."""

    @pytest.mark.asyncio
    async def test_subscription_created_success(self):
        """Test successful subscription creation from webhook."""
        # Arrange
        handler = StripeWebhookHandler(owner=MagicMock())
        subscription_data = {
            "id": "sub_123",
            "customer": "cus_123",
            "status": "active",
            "items": {
                "data": [{
                    "price": {
                        "id": "price_123",
                        "product": "prod_123",
                        "unit_amount": 2999,
                        "currency": "aud",
                        "recurring": {"interval": "month"}
                    }
                }]
            },
            "current_period_start": 1234567890,
            "current_period_end": 1267890123,
            "trial_start": None,
            "trial_end": None
        }

        mock_user = MagicMock()
        mock_user.organization_id = "org_123"
        mock_user.email = "test@example.com"
        mock_user.save = AsyncMock()

        mock_user_query = MagicMock()
        mock_user_query.first = AsyncMock(return_value=mock_user)
        mock_where = MagicMock(return_value=mock_user_query)

        mock_subscription_create = MagicMock()
        mock_subscription_create.create = AsyncMock()

        with patch('cellophanemail.routes.stripe_webhooks.User.objects') as mock_user_objects:
            with patch('cellophanemail.routes.stripe_webhooks.Subscription.objects') as mock_sub_objects:
                mock_user_objects.return_value.where = mock_where
                mock_sub_objects.return_value = mock_subscription_create

                # Act
                await handler._handle_subscription_created(subscription_data)

                # Assert
                mock_subscription_create.create.assert_called_once()
                mock_user.save.assert_called_once()
                assert mock_user.subscription_status == "active"

    @pytest.mark.asyncio
    async def test_subscription_created_user_not_found(self):
        """Test subscription creation when user doesn't exist."""
        # Arrange
        handler = StripeWebhookHandler(owner=MagicMock())
        subscription_data = {
            "id": "sub_123",
            "customer": "cus_nonexistent",
            "status": "active",
            "items": {"data": [{"price": {"id": "price_123", "product": "prod_123", "unit_amount": 2999, "currency": "aud", "recurring": {"interval": "month"}}}]},
            "current_period_start": 1234567890,
            "current_period_end": 1267890123
        }

        mock_user_query = MagicMock()
        mock_user_query.first = AsyncMock(return_value=None)  # No user found
        mock_where = MagicMock(return_value=mock_user_query)

        mock_subscription_create = MagicMock()
        mock_subscription_create.create = AsyncMock()

        with patch('cellophanemail.routes.stripe_webhooks.User.objects') as mock_user_objects:
            with patch('cellophanemail.routes.stripe_webhooks.Subscription.objects') as mock_sub_objects:
                mock_user_objects.return_value.where = mock_where
                mock_sub_objects.return_value = mock_subscription_create

                # Act
                await handler._handle_subscription_created(subscription_data)

                # Assert - should not create subscription if user not found
                mock_subscription_create.create.assert_not_called()


class TestSubscriptionUpdatedWebhook:
    """Test handling of subscription.updated webhook."""

    @pytest.mark.asyncio
    async def test_subscription_updated_success(self):
        """Test successful subscription update from webhook."""
        # Arrange
        handler = StripeWebhookHandler(owner=MagicMock())
        subscription_data = {
            "id": "sub_123",
            "customer": "cus_123",
            "status": "past_due",
            "current_period_start": 1234567890,
            "current_period_end": 1267890123,
            "cancel_at_period_end": True,
            "canceled_at": 1267890120
        }

        mock_subscription = MagicMock()
        mock_subscription.save = AsyncMock()

        mock_sub_query = MagicMock()
        mock_sub_query.first = AsyncMock(return_value=mock_subscription)
        mock_where = MagicMock(return_value=mock_sub_query)

        mock_user = MagicMock()
        mock_user.save = AsyncMock()

        mock_user_query = MagicMock()
        mock_user_query.first = AsyncMock(return_value=mock_user)
        mock_user_where = MagicMock(return_value=mock_user_query)

        with patch('cellophanemail.routes.stripe_webhooks.Subscription.objects') as mock_sub_objects:
            with patch('cellophanemail.routes.stripe_webhooks.User.objects') as mock_user_objects:
                mock_sub_objects.return_value.where = mock_where
                mock_user_objects.return_value.where = mock_user_where

                # Act
                await handler._handle_subscription_updated(subscription_data)

                # Assert
                assert mock_subscription.status == "past_due"
                assert mock_subscription.cancel_at_period_end is True
                mock_subscription.save.assert_called_once()
                assert mock_user.subscription_status == "past_due"
                mock_user.save.assert_called_once()


class TestSubscriptionDeletedWebhook:
    """Test handling of subscription.deleted webhook."""

    @pytest.mark.asyncio
    async def test_subscription_deleted_success(self):
        """Test successful subscription deletion from webhook."""
        # Arrange
        handler = StripeWebhookHandler(owner=MagicMock())
        subscription_data = {
            "id": "sub_123",
            "customer": "cus_123"
        }

        mock_subscription = MagicMock()
        mock_subscription.save = AsyncMock()

        mock_sub_query = MagicMock()
        mock_sub_query.first = AsyncMock(return_value=mock_subscription)
        mock_where = MagicMock(return_value=mock_sub_query)

        mock_user = MagicMock()
        mock_user.save = AsyncMock()

        mock_user_query = MagicMock()
        mock_user_query.first = AsyncMock(return_value=mock_user)
        mock_user_where = MagicMock(return_value=mock_user_query)

        with patch('cellophanemail.routes.stripe_webhooks.Subscription.objects') as mock_sub_objects:
            with patch('cellophanemail.routes.stripe_webhooks.User.objects') as mock_user_objects:
                with patch('cellophanemail.routes.stripe_webhooks.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2025, 1, 15, 12, 0, 0)
                    mock_sub_objects.return_value.where = mock_where
                    mock_user_objects.return_value.where = mock_user_where

                    # Act
                    await handler._handle_subscription_deleted(subscription_data)

                    # Assert
                    assert mock_subscription.status == "canceled"
                    assert mock_subscription.is_active is False
                    mock_subscription.save.assert_called_once()
                    assert mock_user.subscription_status == "canceled"
                    mock_user.save.assert_called_once()


class TestPaymentWebhooks:
    """Test handling of payment success/failure webhooks."""

    @pytest.mark.asyncio
    async def test_payment_succeeded(self):
        """Test payment succeeded webhook is logged."""
        # Arrange
        handler = StripeWebhookHandler(owner=MagicMock())
        invoice_data = {
            "id": "in_123",
            "customer": "cus_123",
            "amount_paid": 2999,
            "status": "paid"
        }

        with patch('cellophanemail.routes.stripe_webhooks.logger') as mock_logger:
            # Act
            await handler._handle_payment_succeeded(invoice_data)

            # Assert
            mock_logger.info.assert_called_once()
            assert "Payment succeeded" in mock_logger.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_payment_failed_updates_user_status(self):
        """Test payment failed webhook updates user to past_due."""
        # Arrange
        handler = StripeWebhookHandler(owner=MagicMock())
        invoice_data = {
            "id": "in_123",
            "customer": "cus_123"
        }

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.save = AsyncMock()

        mock_user_query = MagicMock()
        mock_user_query.first = AsyncMock(return_value=mock_user)
        mock_where = MagicMock(return_value=mock_user_query)

        with patch('cellophanemail.routes.stripe_webhooks.User.objects') as mock_user_objects:
            with patch('cellophanemail.routes.stripe_webhooks.logger') as mock_logger:
                mock_user_objects.return_value.where = mock_where

                # Act
                await handler._handle_payment_failed(invoice_data)

                # Assert
                assert mock_user.subscription_status == "past_due"
                mock_user.save.assert_called_once()
                mock_logger.warning.assert_called_once()
