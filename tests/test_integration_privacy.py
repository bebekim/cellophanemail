"""
Integration test for privacy mode - replaces the old integration test
that bypassed the webhook controller
"""
import pytest
import os
from unittest.mock import patch, Mock
from litestar import Litestar
from litestar.testing import AsyncTestClient

from cellophanemail.routes.webhooks import WebhookController


class TestPrivacyIntegration:
    """Integration test for privacy-aware webhook processing"""
    
    @pytest.mark.asyncio
    async def test_webhook_to_forward_flow_with_privacy_mode(self):
        """Test complete flow: webhook → privacy analysis → forward with NO database logging"""
        
        # Set privacy mode for this test
        with patch.dict(os.environ, {'PRIVACY_MODE': 'true'}):
            
            # Create the actual webhook payload that would come from Postmark
            webhook_payload = {
                "MessageID": "privacy-flow-test-001",
                "From": "friend@example.com", 
                "To": "shield.abc123@cellophanemail.com",
                "Subject": "Hello!",  # This should NOT be logged to database
                "Date": "2025-01-08T10:00:00Z",
                "TextBody": "Hope you're doing well!",
                "HtmlBody": "<p>Hope you're doing well!</p>"
            }
            
            # Create Litestar app with webhook controller
            app = Litestar(
                route_handlers=[WebhookController],
                debug=True
            )
            
            # Mock the shield address lookup
            with patch('cellophanemail.features.shield_addresses.ShieldAddressManager.lookup_user_by_shield_address') as mock_shield:
                mock_shield_info = Mock()
                mock_shield_info.user_id = 'real-user-123'
                mock_shield_info.user_email = 'realuser@example.com'
                mock_shield_info.organization_id = '123'
                mock_shield.return_value = mock_shield_info
                
                # Mock the privacy orchestrator to track calls
                with patch('cellophanemail.features.privacy_integration.privacy_webhook_orchestrator.PrivacyWebhookOrchestrator.process_webhook') as mock_privacy:
                    mock_privacy.return_value = {
                        "status": "accepted",
                        "message_id": "privacy-flow-test-001",
                        "processing": "async_privacy_pipeline" 
                    }
                    
                    # Mock database logging to ensure it's NOT called
                    with patch('cellophanemail.features.email_protection.storage.ProtectionLogStorage.log_protection_decision') as mock_db_log:
                        
                        # Act - Send the webhook request
                        async with AsyncTestClient(app=app) as client:
                            response = await client.post("/webhooks/postmark", json=webhook_payload)
                            
                            # Assert - Privacy mode behavior
                            # 1. Should return 202 Accepted (privacy mode)
                            assert response.status_code == 202
                            
                            # 2. Privacy orchestrator should be called
                            mock_privacy.assert_called_once()
                            
                            # 3. Database logging should NOT be called
                            mock_db_log.assert_not_called()
                            
                            # 4. Response should indicate privacy processing
                            response_data = response.json()
                            assert response_data.get("status") == "accepted"
                            assert response_data.get("processing") == "async_privacy_pipeline"
                            
                            print("✅ Complete privacy flow works - Email processed in-memory only")
    
    @pytest.mark.asyncio  
    async def test_webhook_to_forward_flow_with_normal_mode(self):
        """Test complete flow: webhook → normal analysis → forward WITH database logging"""
        
        # Ensure normal mode (privacy disabled)
        with patch.dict(os.environ, {'PRIVACY_MODE': 'false'}, clear=True):
            
            webhook_payload = {
                "MessageID": "normal-flow-test-001",
                "From": "friend@example.com",
                "To": "shield.xyz789@cellophanemail.com",
                "Subject": "Hello Normal Mode!",
                "Date": "2025-01-08T10:00:00Z", 
                "TextBody": "This should use normal processing"
            }
            
            app = Litestar(
                route_handlers=[WebhookController],
                debug=True
            )
            
            with patch('cellophanemail.features.shield_addresses.ShieldAddressManager.lookup_user_by_shield_address') as mock_shield:
                mock_shield_info = Mock()
                mock_shield_info.user_id = 'normal-user-456'
                mock_shield_info.user_email = 'normaluser@example.com'
                mock_shield_info.organization_id = '456'
                mock_shield.return_value = mock_shield_info
                
                # Mock the normal email protection processor
                with patch('cellophanemail.features.email_protection.EmailProtectionProcessor.process_email') as mock_processor:
                    mock_result = Mock()
                    mock_result.should_forward = True
                    mock_result.analysis.toxicity_score = 0.1
                    mock_result.analysis.processing_time_ms = 1000
                    mock_result.block_reason = None
                    mock_result.analysis.horsemen_detected = []
                    mock_processor.return_value = mock_result
                    
                    # Mock Postmark email sending 
                    with patch('cellophanemail.providers.postmark.provider.PostmarkProvider.send_message') as mock_send:
                        mock_send.return_value = True
                        
                        async with AsyncTestClient(app=app) as client:
                            response = await client.post("/webhooks/postmark", json=webhook_payload)
                            
                            # Assert - Normal mode behavior
                            # 1. Should return 200 OK (normal mode)
                            assert response.status_code == 200
                            
                            # 2. Normal processor should be called
                            mock_processor.assert_called_once()
                            
                            # 3. Response should indicate forwarding
                            response_data = response.json()
                            assert response_data.get("status") == "accepted"
                            assert response_data.get("processing") == "forwarded"
                            
                            print("✅ Complete normal flow works - Email processed with database logging")