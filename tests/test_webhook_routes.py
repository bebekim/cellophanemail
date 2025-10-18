"""Tests for webhook routes."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from litestar import Litestar
from litestar.testing import AsyncTestClient

from cellophanemail.routes.webhooks import WebhookController
from cellophanemail.core.webhook_models import PostmarkWebhookPayload


@pytest.fixture
def webhook_app():
    """Create Litestar app with WebhookController for testing."""
    app = Litestar(route_handlers=[WebhookController])
    return app


@pytest.fixture
def sample_postmark_payload():
    """Sample Postmark webhook payload."""
    return {
        "MessageID": "msg-123",
        "From": "sender@example.com",
        "FromName": "Test Sender",
        "To": "shield@cellophanemail.com",
        "Subject": "Test Email",
        "Date": "2025-10-17T10:30:00Z",
        "TextBody": "This is a test email body",
        "HtmlBody": "<p>This is a test email body</p>",
        "Tag": "",
        "Headers": [
            {"Name": "Content-Type", "Value": "text/html"},
            {"Name": "Message-ID", "Value": "<msg-123@example.com>"}
        ],
        "Attachments": []
    }


class TestPostmarkWebhook:
    """Test Postmark webhook endpoint."""

    @pytest.mark.asyncio
    async def test_postmark_webhook_success(self, webhook_app, sample_postmark_payload):
        """Test successful Postmark webhook processing."""
        # Mock shield address manager
        mock_shield_info = MagicMock()
        mock_shield_info.user_id = "user-123"
        mock_shield_info.user_email = "real@example.com"
        mock_shield_info.organization_id = None

        # Mock processing result
        mock_processing_result = MagicMock()
        mock_processing_result.response_data = {
            "status": "delivered",
            "message_id": "msg-123"
        }
        mock_processing_result.status_code = 200

        with patch('cellophanemail.routes.webhooks.ShieldAddressManager') as MockShield:
            mock_shield_instance = MockShield.return_value
            mock_shield_instance.lookup_user_by_shield_address = AsyncMock(return_value=mock_shield_info)

            with patch('cellophanemail.routes.webhooks.ProcessingStrategyManager') as MockStrategy:
                mock_strategy_instance = MockStrategy.return_value
                mock_strategy_instance.process_email = AsyncMock(return_value=mock_processing_result)

                async with AsyncTestClient(app=webhook_app) as client:
                    response = await client.post(
                        "/webhooks/postmark",
                        json=sample_postmark_payload
                    )

                    # Webhook returns 202 (Accepted) for async processing
                    assert response.status_code in [200, 202]
                    # Note: In real implementation, this goes through privacy pipeline
                    # which may return different status codes

    @pytest.mark.asyncio
    async def test_postmark_webhook_invalid_domain(self, webhook_app, sample_postmark_payload):
        """Test Postmark webhook rejects invalid domain."""
        sample_postmark_payload["To"] = "shield@wrongdomain.com"

        async with AsyncTestClient(app=webhook_app) as client:
            response = await client.post(
                "/webhooks/postmark",
                json=sample_postmark_payload
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert "Invalid domain" in data["error"]
            assert data["message_id"] == "msg-123"

    @pytest.mark.asyncio
    async def test_postmark_webhook_shield_not_found(self, webhook_app, sample_postmark_payload):
        """Test Postmark webhook handles unknown shield address."""
        with patch('cellophanemail.routes.webhooks.ShieldAddressManager') as MockShield:
            mock_shield_instance = MockShield.return_value
            mock_shield_instance.lookup_user_by_shield_address = AsyncMock(return_value=None)

            async with AsyncTestClient(app=webhook_app) as client:
                response = await client.post(
                    "/webhooks/postmark",
                    json=sample_postmark_payload
                )

                assert response.status_code == 404
                data = response.json()
                assert "error" in data
                assert "not found" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_postmark_webhook_normalizes_address(self, webhook_app, sample_postmark_payload):
        """Test Postmark webhook normalizes shield address (lowercase, trim)."""
        sample_postmark_payload["To"] = "  SHIELD@CELLOPHANEMAIL.COM  "

        mock_shield_info = MagicMock()
        mock_shield_info.user_id = "user-123"
        mock_shield_info.user_email = "real@example.com"
        mock_shield_info.organization_id = None

        mock_processing_result = MagicMock()
        mock_processing_result.response_data = {"status": "delivered"}
        mock_processing_result.status_code = 200

        with patch('cellophanemail.routes.webhooks.ShieldAddressManager') as MockShield:
            mock_shield_instance = MockShield.return_value
            mock_shield_instance.lookup_user_by_shield_address = AsyncMock(return_value=mock_shield_info)

            with patch('cellophanemail.routes.webhooks.ProcessingStrategyManager') as MockStrategy:
                mock_strategy_instance = MockStrategy.return_value
                mock_strategy_instance.process_email = AsyncMock(return_value=mock_processing_result)

                async with AsyncTestClient(app=webhook_app) as client:
                    response = await client.post(
                        "/webhooks/postmark",
                        json=sample_postmark_payload
                    )

                    # Verify lookup was called with normalized address
                    mock_shield_instance.lookup_user_by_shield_address.assert_called_once()
                    call_args = mock_shield_instance.lookup_user_by_shield_address.call_args
                    assert call_args[0][0] == "shield@cellophanemail.com"


class TestGmailWebhook:
    """Test Gmail webhook endpoint."""

    @pytest.mark.asyncio
    async def test_gmail_webhook_success(self, webhook_app):
        """Test Gmail webhook accepts notifications."""
        gmail_payload = {
            "message": {
                "data": "base64-encoded-data",
                "messageId": "gmail-msg-123"
            }
        }

        async with AsyncTestClient(app=webhook_app) as client:
            response = await client.post(
                "/webhooks/gmail",
                json=gmail_payload
            )

            assert response.status_code == 201  # Litestar default for POST
            data = response.json()
            assert data["status"] == "accepted"
            assert data["notification"] == "processed"

    @pytest.mark.asyncio
    async def test_gmail_webhook_empty_payload(self, webhook_app):
        """Test Gmail webhook handles empty payload."""
        async with AsyncTestClient(app=webhook_app) as client:
            response = await client.post(
                "/webhooks/gmail",
                json={}
            )

            assert response.status_code == 201  # Litestar default for POST


class TestWebhookTest:
    """Test webhook test endpoint."""

    @pytest.mark.asyncio
    async def test_webhook_test_endpoint(self, webhook_app):
        """Test the test webhook endpoint."""
        test_payload = {
            "test_field": "test_value",
            "number": 123
        }

        async with AsyncTestClient(app=webhook_app) as client:
            response = await client.post(
                "/webhooks/test",
                json=test_payload
            )

            assert response.status_code == 201  # Litestar default for POST
            data = response.json()
            assert data["status"] == "received"
            assert data["test"] == "successful"
            assert "data_received" in data

    @pytest.mark.asyncio
    async def test_webhook_test_empty_payload(self, webhook_app):
        """Test test endpoint with empty payload."""
        async with AsyncTestClient(app=webhook_app) as client:
            response = await client.post(
                "/webhooks/test",
                json={}
            )

            assert response.status_code == 201  # Litestar default for POST
            data = response.json()
            assert data["status"] == "received"


class TestWebhookHelperMethods:
    """Test webhook controller helper methods."""

    def test_extract_shield_address(self, webhook_app):
        """Test shield address extraction."""
        controller = WebhookController(webhook_app)

        mock_payload = MagicMock()
        mock_payload.To = "  TEST@CELLOPHANEMAIL.COM  "

        address = controller._extract_shield_address(mock_payload)

        assert address == "test@cellophanemail.com"

    def test_validate_domain_valid(self, webhook_app):
        """Test domain validation with valid domain."""
        controller = WebhookController(webhook_app)

        # Should not raise exception
        controller._validate_domain("shield@cellophanemail.com", "msg-123")

    def test_validate_domain_invalid(self, webhook_app):
        """Test domain validation with invalid domain."""
        controller = WebhookController(webhook_app)

        with pytest.raises(ValueError):
            controller._validate_domain("shield@wrongdomain.com", "msg-123")

    @pytest.mark.asyncio
    async def test_get_user_success(self, webhook_app):
        """Test user lookup by shield address."""
        controller = WebhookController(webhook_app)

        mock_shield_info = MagicMock()
        mock_shield_info.user_id = "user-123"
        mock_shield_info.user_email = "real@example.com"
        mock_shield_info.organization_id = "org-456"

        with patch('cellophanemail.routes.webhooks.ShieldAddressManager') as MockShield:
            mock_shield_instance = MockShield.return_value
            mock_shield_instance.lookup_user_by_shield_address = AsyncMock(return_value=mock_shield_info)

            user = await controller._get_user("shield@cellophanemail.com", "msg-123")

            assert user["id"] == "user-123"
            assert user["email"] == "real@example.com"
            assert user["organization"] == "org-456"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, webhook_app):
        """Test user lookup when shield address not found."""
        controller = WebhookController(webhook_app)

        with patch('cellophanemail.routes.webhooks.ShieldAddressManager') as MockShield:
            mock_shield_instance = MockShield.return_value
            mock_shield_instance.lookup_user_by_shield_address = AsyncMock(return_value=None)

            with pytest.raises(ValueError):
                await controller._get_user("notfound@cellophanemail.com", "msg-123")

    def test_error_response(self, webhook_app):
        """Test error response formatting."""
        controller = WebhookController(webhook_app)

        response = controller._error_response("Test error", "msg-123", 404)

        assert response.status_code == 404
        assert response.content["error"] == "Test error"
        assert response.content["message_id"] == "msg-123"
