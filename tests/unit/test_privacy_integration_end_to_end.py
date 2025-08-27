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
    async def test_normal_mode_allows_database_logging_in_webhook_flow(self):
        """
        RED TEST: When PRIVACY_MODE=false, webhook flow should log to database (current behavior)
        This verifies backward compatibility
        """
        # Arrange - Ensure privacy mode is disabled
        with patch.dict(os.environ, {'PRIVACY_MODE': 'false'}, clear=True):
            
            payload = {
                "MessageID": "normal-test-001", 
                "From": "sender@example.com",
                "To": "shield.test456@cellophanemail.com",
                "Subject": "Normal Mode Email",
                "Date": "2025-01-08T10:00:00Z",
                "TextBody": "This should use normal processing"
            }
            
            app = Litestar(
                route_handlers=[WebhookController],
                debug=True
            )
            
            with patch('cellophanemail.features.shield_addresses.ShieldAddressManager.lookup_user_by_shield_address') as mock_shield:
                # Return proper mock object with attributes
                mock_shield_info = Mock()
                mock_shield_info.user_id = 'user-456'  
                mock_shield_info.user_email = 'user@example.com'
                mock_shield_info.organization_id = '123'
                mock_shield.return_value = mock_shield_info
                
                with patch('cellophanemail.features.email_protection.EmailProtectionProcessor.process_email') as mock_protection:
                    # Mock normal processing response
                    mock_result = Mock()
                    mock_result.should_forward = True
                    mock_result.analysis.toxicity_score = 0.1
                    mock_result.analysis.processing_time_ms = 1000
                    mock_result.block_reason = None
                    mock_result.analysis.horsemen_detected = []
                    mock_protection.return_value = mock_result
                    
                    async with AsyncTestClient(app=app) as client:
                        response = await client.post("/webhooks/postmark", json=payload)
                        
                        # Assert
                        # 1. Should return 200 OK (normal processing)
                        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
                        
                        # 2. Normal processing should be called
                        mock_protection.assert_called_once()
                        
                        # 3. Response should indicate normal processing
                        response_data = response.json()
                        assert response_data.get("status") == "forwarded" or "message_id" in response_data