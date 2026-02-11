"""
TDD CYCLE 2 - RED PHASE: End-to-end privacy integration test
Test that PRIVACY_MODE=true prevents database logging in actual webhook flow
"""
import pytest
import os
from unittest.mock import patch, Mock
from litestar import Litestar
from litestar.testing import AsyncTestClient

from cellophanemail.core.webhook_models import PostmarkWebhookPayload
from cellophanemail.routes.webhooks import WebhookController


class TestPrivacyIntegrationEndToEnd:
    """Test actual end-to-end privacy integration"""
    
    @pytest.mark.asyncio
    async def test_privacy_mode_prevents_database_logging_in_webhook_flow(self):
        """
        RED TEST: When PRIVACY_MODE=true, webhook flow should NOT log to database
        This tests the actual end-to-end integration, not just unit tests
        """
        # Arrange - Set privacy mode environment variable
        with patch.dict(os.environ, {'PRIVACY_MODE': 'true'}):
            
            # Create real webhook payload
            payload = {
                "MessageID": "privacy-test-001",
                "From": "sender@example.com",
                "To": "shield.test123@cellophanemail.com",  
                "Subject": "PRIVATE EMAIL SUBJECT",  # This should NOT be logged
                "Date": "2025-01-08T10:00:00Z",
                "TextBody": "This private content should not be logged to database",
                "HtmlBody": "<p>This private content should not be logged to database</p>"
            }
            
            # Create Litestar app with webhook controller
            app = Litestar(
                route_handlers=[WebhookController],
                debug=True
            )
            
            # Mock the shield address lookup to simulate existing user
            with patch('cellophanemail.features.shield_addresses.ShieldAddressManager.lookup_user_by_shield_address') as mock_shield:
                # Return proper mock object with attributes
                mock_shield_info = Mock()
                mock_shield_info.user_id = 'user-123'
                mock_shield_info.user_email = 'user@example.com'
                mock_shield_info.organization_id = '123'
                mock_shield.return_value = mock_shield_info
                
                # Mock database logging to track if it gets called
                with patch('cellophanemail.features.email_protection.storage.ProtectionLogStorage.log_protection_decision') as mock_db_log:
                    
                    # Act - Send actual HTTP request to webhook endpoint
                    async with AsyncTestClient(app=app) as client:
                        response = await client.post("/webhooks/postmark", json=payload)
                        
                        # Assert
                        # 1. Should return 202 Accepted (privacy mode async processing)
                        assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"
                        
                        # 2. Database logging should NOT be called
                        mock_db_log.assert_not_called(), "Database logging was called despite PRIVACY_MODE=true"
                        
                        # 3. Response should indicate privacy processing
                        response_data = response.json()
                        assert "privacy" in str(response_data).lower() or "accepted" in str(response_data).lower()
    
    @pytest.mark.asyncio
    async def test_privacy_mode_false_still_uses_privacy_pipeline(self):
        """
        Test: Even with PRIVACY_MODE=false, the system now uses the privacy-only pipeline.
        ProcessingStrategyManager is privacy-only (no normal/legacy mode).
        """
        # Arrange - Privacy mode false, but pipeline is still privacy-only
        with patch.dict(os.environ, {'PRIVACY_MODE': 'false'}, clear=True):

            payload = {
                "MessageID": "normal-test-001",
                "From": "sender@example.com",
                "To": "shield.test456@cellophanemail.com",
                "Subject": "Normal Mode Email",
                "Date": "2025-01-08T10:00:00Z",
                "TextBody": "This should use privacy processing"
            }

            app = Litestar(
                route_handlers=[WebhookController],
                debug=True
            )

            with patch('cellophanemail.features.shield_addresses.ShieldAddressManager.lookup_user_by_shield_address') as mock_shield:
                mock_shield_info = Mock()
                mock_shield_info.user_id = 'user-456'
                mock_shield_info.user_email = 'user@example.com'
                mock_shield_info.organization_id = '123'
                mock_shield.return_value = mock_shield_info

                with patch('cellophanemail.features.privacy_integration.privacy_webhook_orchestrator.PrivacyWebhookOrchestrator.process_webhook') as mock_privacy:
                    mock_privacy.return_value = {
                        "status": "accepted",
                        "message_id": "normal-test-001",
                        "processing": "async_privacy_pipeline"
                    }

                    async with AsyncTestClient(app=app) as client:
                        response = await client.post("/webhooks/postmark", json=payload)

                        # Assert
                        # 1. Should return 202 Accepted (privacy-only pipeline)
                        assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"

                        # 2. Privacy orchestrator should be called
                        mock_privacy.assert_called_once()

                        # 3. Response should indicate privacy processing
                        response_data = response.json()
                        assert response_data.get("status") == "accepted"