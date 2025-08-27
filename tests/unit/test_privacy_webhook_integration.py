"""
TDD CYCLE 1: Privacy Webhook Integration Tests
Test that webhook uses privacy pipeline instead of database storage
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
from cellophanemail.features.email_protection.memory_manager import MemoryManager


class TestPrivacyWebhookIntegration:
    """Test privacy-focused webhook processing without database storage"""
    
    @pytest.mark.asyncio
    async def test_webhook_uses_privacy_pipeline_not_database(self):
        """
        RED TEST: Webhook should use InMemoryProcessor instead of database storage
        This test verifies the privacy pipeline is used instead of database
        """
        # Arrange
        from cellophanemail.features.privacy_integration.privacy_webhook_orchestrator import (
            PrivacyWebhookOrchestrator
        )
        
        # Create mock webhook payload (similar to Postmark webhook)
        from cellophanemail.core.webhook_models import PostmarkWebhookPayload
        webhook_payload = PostmarkWebhookPayload(
            MessageID="test-123",
            From="sender@example.com",
            To="shield@cellophanemail.com",
            Subject="Test Email",
            Date="2025-01-08T10:00:00Z",
            TextBody="This is a test email content",
            HtmlBody="<p>This is a test email content</p>"
        )
        
        # Create orchestrator (fresh instance has clean memory)
        orchestrator = PrivacyWebhookOrchestrator()
        
        # Mock the database to ensure it's NOT called
        with patch('cellophanemail.features.email_protection.storage.ProtectionLogStorage.log_protection_decision') as mock_db:
            # Act
            result = await orchestrator.process_webhook(webhook_payload)
            
            # Assert
            # 1. Database should NOT be called to store content
            mock_db.assert_not_called()
            
            # 2. Result should indicate success (status: accepted)
            assert result["status"] == "accepted"
            assert result["message_id"] == "test-123"
            assert result["processing"] == "async_privacy_pipeline"
            
            # 3. Email should be in memory manager (not database)
            stats = orchestrator.memory_manager.get_stats()
            assert stats['current_emails'] > 0
            
            # 4. Email should be retrievable by message ID and have proper TTL
            stored_email = orchestrator.memory_manager.get_email("test-123")
            assert stored_email is not None
            assert isinstance(stored_email, EphemeralEmail)
            assert stored_email.message_id == "test-123"
            assert stored_email.ttl_seconds == 300  # 5 minutes
            assert not stored_email.is_expired  # Should not be expired immediately
    
    @pytest.mark.asyncio
    async def test_privacy_orchestrator_implements_interface(self):
        """
        REFACTOR TEST: Ensure PrivacyWebhookOrchestrator follows interface contract
        """
        from cellophanemail.features.privacy_integration.privacy_webhook_orchestrator import (
            PrivacyWebhookOrchestrator
        )
        from cellophanemail.features.privacy_integration.orchestrator_interface import (
            BaseWebhookOrchestrator, WebhookOrchestrator
        )
        
        orchestrator = PrivacyWebhookOrchestrator()
        
        # Should inherit from base class
        assert isinstance(orchestrator, BaseWebhookOrchestrator)
        
        # Should implement the protocol methods
        assert hasattr(orchestrator, 'process_webhook')
        assert callable(orchestrator.process_webhook)
        
        # Should have standardized response creation
        assert hasattr(orchestrator, '_create_response')
        assert callable(orchestrator._create_response)