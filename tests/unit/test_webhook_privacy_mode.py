"""
Webhook Controller Privacy Mode Integration Tests
Test that main webhook controller integrates with privacy strategy
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import os
from litestar.testing import TestClient

from cellophanemail.core.webhook_models import PostmarkWebhookPayload
from cellophanemail.app import create_app


class TestWebhookControllerPrivacyMode:
    """Test main webhook controller privacy mode integration"""
    
    def test_strategy_manager_detects_privacy_mode_enabled(self):
        """
        Test: Should configure privacy strategy when PRIVACY_MODE is 'true'
        """
        # Arrange - Set privacy mode environment variable
        with patch.dict(os.environ, {'PRIVACY_MODE': 'true'}):
            from cellophanemail.routes.webhooks import WebhookController
            
            # Act - Create controller (which initializes strategy manager)
            controller = WebhookController(owner=Mock())
            
            # Assert - Strategy manager should be configured for privacy mode
            assert controller.strategy_manager.config.privacy_enabled is True
            assert controller.strategy_manager.config.mode.value == "privacy"
    
    def test_strategy_manager_detects_privacy_mode_disabled_false(self):
        """
        Test: Should configure normal strategy when PRIVACY_MODE is 'false'
        """
        # Arrange - Set privacy mode to false
        with patch.dict(os.environ, {'PRIVACY_MODE': 'false'}):
            from cellophanemail.routes.webhooks import WebhookController
            
            # Act
            controller = WebhookController(owner=Mock())
            
            # Assert
            assert controller.strategy_manager.config.privacy_enabled is False
            assert controller.strategy_manager.config.mode.value == "normal"
    
    def test_strategy_manager_defaults_to_normal_mode_when_not_set(self):
        """
        Test: Should default to normal mode when PRIVACY_MODE is not set
        """
        # Arrange - Remove PRIVACY_MODE if it exists
        env_without_privacy = {k: v for k, v in os.environ.items() if k != 'PRIVACY_MODE'}
        with patch.dict(os.environ, env_without_privacy, clear=True):
            from cellophanemail.routes.webhooks import WebhookController
            
            # Act
            controller = WebhookController(owner=Mock())
            
            # Assert
            assert controller.strategy_manager.config.privacy_enabled is False
            assert controller.strategy_manager.config.mode.value == "normal"

    def test_webhook_controller_uses_privacy_mode_when_enabled(self):
        """
        Integration Test: Main webhook controller should use PrivacyWebhookOrchestrator 
        when PRIVACY_MODE environment variable is set to true
        """
        # Arrange - Set privacy mode environment variable
        with patch.dict(os.environ, {'PRIVACY_MODE': 'true'}):
            from cellophanemail.features.privacy_integration.privacy_webhook_orchestrator import (
                PrivacyWebhookOrchestrator
            )
            
            # Create test payload
            payload = {
                "MessageID": "test-privacy-mode-123",
                "From": "sender@example.com", 
                "To": "shield.test123@cellophanemail.com",
                "Subject": "Test Privacy Mode Email",
                "Date": "2025-01-08T10:00:00Z",
                "TextBody": "This email should use privacy mode processing",
                "HtmlBody": "<p>This email should use privacy mode processing</p>"
            }
            
            # Mock the privacy orchestrator to track if it's called
            with patch.object(PrivacyWebhookOrchestrator, 'process_webhook') as mock_privacy_process:
                mock_privacy_process.return_value = {
                    "status": "accepted",
                    "message_id": "test-privacy-mode-123", 
                    "processing": "async_privacy_pipeline"
                }
                
                # Mock the shield address lookup that happens before strategy processing
                with patch('cellophanemail.features.shield_addresses.ShieldAddressManager.lookup_user_by_shield_address') as mock_shield:
                    mock_shield.return_value = Mock(
                        user_id='user123',
                        user_email='user@example.com',
                        organization_id='org123'
                    )
                    
                    # Create test client
                    app = create_app()
                    test_client = TestClient(app=app)
                    
                    # Act - Call the main webhook endpoint via HTTP
                    response = test_client.post("/webhooks/postmark", json=payload)
                
                # Assert
                # 1. Privacy orchestrator should be called through strategy
                mock_privacy_process.assert_called_once()
                
                # 2. Response should be 202 Accepted for async processing
                assert response.status_code == 202
                
                # 3. Response should indicate accepted status
                response_data = response.json()
                assert response_data["status"] == "accepted"

    def test_webhook_controller_uses_normal_mode_when_privacy_disabled(self):
        """
        Integration Test: Main webhook controller should use normal EmailProtectionProcessor 
        when PRIVACY_MODE is false or not set
        """
        # Arrange - Ensure privacy mode is disabled
        with patch.dict(os.environ, {'PRIVACY_MODE': 'false'}, clear=False):
            from cellophanemail.features.privacy_integration.privacy_webhook_orchestrator import (
                PrivacyWebhookOrchestrator
            )
            
            payload = {
                "MessageID": "test-normal-mode-123",
                "From": "sender@example.com",
                "To": "shield.test456@cellophanemail.com", 
                "Subject": "Test Normal Mode Email",
                "Date": "2025-01-08T10:00:00Z",
                "TextBody": "This email should use normal processing"
            }
            
            # Mock the privacy orchestrator to ensure it's NOT called
            with patch.object(PrivacyWebhookOrchestrator, 'process_webhook') as mock_privacy_process:
                # Mock normal processing components
                with patch('cellophanemail.features.shield_addresses.ShieldAddressManager.lookup_user_by_shield_address') as mock_shield:
                    with patch('cellophanemail.features.email_protection.EmailProtectionProcessor.process_email') as mock_protection:
                        
                        # Setup normal flow mocks
                        mock_shield.return_value = Mock(
                            user_id='user123',
                            user_email='user@example.com',
                            organization_id='org123'
                        )
                        
                        mock_result = Mock()
                        mock_result.should_forward = True
                        mock_result.analysis = Mock()
                        mock_result.analysis.toxicity_score = 0.1
                        mock_result.analysis.processing_time_ms = 1000
                        mock_result.analysis.horsemen_detected = []
                        mock_result.block_reason = None
                        mock_protection.return_value = mock_result
                        
                        # Create test client
                        app = create_app()
                        test_client = TestClient(app=app)
                        
                        # Act - Call the main webhook endpoint via HTTP
                        response = test_client.post("/webhooks/postmark", json=payload)
                        
                        # Assert
                        # 1. Privacy orchestrator should NOT be called
                        mock_privacy_process.assert_not_called()
                        
                        # 2. Normal protection processor should be called
                        mock_protection.assert_called_once()
                        
                        # 3. Response should be 200 OK for normal processing
                        assert response.status_code == 200