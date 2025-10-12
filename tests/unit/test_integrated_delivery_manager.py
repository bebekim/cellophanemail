"""
TDD RED PHASE: IntegratedDeliveryManager Tests
Tests for integrating privacy pipeline with actual email delivery (Postmark/SMTP).
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
from cellophanemail.features.email_protection.in_memory_processor import ProcessingResult, ProtectionAction
from cellophanemail.features.email_protection.email_composition_strategy import DeliveryConfiguration

# Try to import integrated delivery components (should fail initially - RED phase)
try:
    from cellophanemail.features.email_protection.integrated_delivery_manager import (
        IntegratedDeliveryManager,
        EnhancedDeliveryResult
    )
    INTEGRATED_DELIVERY_AVAILABLE = True
except ImportError:
    INTEGRATED_DELIVERY_AVAILABLE = False


class TestIntegratedDeliveryManager:
    """Test integrated delivery manager connecting privacy pipeline to email senders."""
    
    def test_integrated_delivery_modules_exist(self):
        """
        RED TEST: Integrated delivery modules should exist
        """
        assert INTEGRATED_DELIVERY_AVAILABLE, \
            "IntegratedDeliveryManager modules must exist"
    
    @pytest.mark.skipif(not INTEGRATED_DELIVERY_AVAILABLE, reason="Integrated delivery modules not available")
    @pytest.mark.asyncio
    async def test_deliver_clean_email_success(self):
        """
        RED TEST: Should deliver clean email successfully through Postmark sender
        """
        # Configure delivery for Postmark
        config = DeliveryConfiguration(
            sender_type="postmark",
            config={
                "POSTMARK_API_TOKEN": "test-token-123",
                "SMTP_DOMAIN": "cellophanemail.com",
                "EMAIL_USERNAME": "noreply"
            },
            service_domain="cellophanemail.com",
            max_retries=3
        )
        
        # Create test data
        original_email = EphemeralEmail(
            message_id="delivery-test-001",
            from_address="alice@example.com",
            to_addresses=["user@example.com"],
            subject="Test Clean Email",
            text_body="This is a clean test email",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.FORWARD_CLEAN,
            toxicity_score=0.12,
            processed_content="This is a clean test email",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=150
        )
        
        # Mock email sender to avoid real API calls
        with patch('cellophanemail.core.email_delivery.factory.EmailSenderFactory.create_sender') as mock_factory:
            mock_sender = AsyncMock()
            mock_sender.send_email.return_value = True  # Simulate successful delivery
            mock_factory.return_value = mock_sender
            
            # Test delivery
            delivery_manager = IntegratedDeliveryManager(config)
            result = await delivery_manager.deliver_email(processing_result, original_email)
        
        # Assertions
        assert isinstance(result, EnhancedDeliveryResult)
        assert result.success == True
        assert result.attempts >= 1
        assert result.protection_action == ProtectionAction.FORWARD_CLEAN
        assert result.toxicity_score == 0.12
        assert result.error_message is None
        assert result.email_sender_used == "postmark"
        assert result.delivery_time_ms is not None
    
    @pytest.mark.skipif(not INTEGRATED_DELIVERY_AVAILABLE, reason="Integrated delivery modules not available")
    @pytest.mark.asyncio
    async def test_deliver_redacted_email_success(self):
        """
        RED TEST: Should deliver redacted email with appropriate headers and content
        """
        config = DeliveryConfiguration(
            sender_type="postmark",
            config={
                "POSTMARK_API_TOKEN": "test-token-456",
                "SMTP_DOMAIN": "cellophanemail.com", 
                "EMAIL_USERNAME": "protection"
            },
            service_domain="cellophanemail.com"
        )
        
        original_email = EphemeralEmail(
            message_id="delivery-test-002",
            from_address="suspicious@example.com",
            to_addresses=["user@example.com"],
            subject="Suspicious Content",
            text_body="This had bad words that got filtered",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.REDACT_HARMFUL,
            toxicity_score=0.72,
            processed_content="This had [REDACTED] words that got filtered",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=280
        )
        
        # Mock email sender
        with patch('cellophanemail.core.email_delivery.factory.EmailSenderFactory.create_sender') as mock_factory:
            mock_sender = AsyncMock()
            mock_sender.send_email.return_value = True
            mock_factory.return_value = mock_sender
            
            delivery_manager = IntegratedDeliveryManager(config)
            result = await delivery_manager.deliver_email(processing_result, original_email)
        
        # Should succeed with redacted content
        assert result.success == True
        assert result.protection_action == ProtectionAction.REDACT_HARMFUL
        assert result.toxicity_score == 0.72
        assert result.email_sender_used == "postmark"
    
    @pytest.mark.skipif(not INTEGRATED_DELIVERY_AVAILABLE, reason="Integrated delivery modules not available")
    @pytest.mark.asyncio
    async def test_no_delivery_for_blocked_emails(self):
        """
        RED TEST: Should skip delivery for blocked emails and return success
        """
        config = DeliveryConfiguration(
            sender_type="postmark",
            config={"POSTMARK_API_TOKEN": "test-token"},
            service_domain="cellophanemail.com"
        )
        
        original_email = EphemeralEmail(
            message_id="blocked-test-001",
            from_address="malicious@spam.com",
            to_addresses=["user@example.com"],
            subject="Totally Malicious Email",
            text_body="This email is completely toxic",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.BLOCK_ENTIRELY,
            toxicity_score=0.95,
            processed_content="",  # Empty for blocked content
            requires_delivery=False,  # No delivery needed
            delivery_targets=[],
            processing_time_ms=200
        )
        
        # Mock email sender (though it shouldn't be used for blocked emails)
        with patch('cellophanemail.core.email_delivery.factory.EmailSenderFactory.create_sender') as mock_factory:
            mock_sender = AsyncMock()
            mock_factory.return_value = mock_sender
            
            delivery_manager = IntegratedDeliveryManager(config)
            result = await delivery_manager.deliver_email(processing_result, original_email)
        
        # Should "succeed" by not delivering
        assert result.success == True
        assert result.attempts == 0
        assert result.protection_action == ProtectionAction.BLOCK_ENTIRELY
        assert result.error_message == "No delivery required"
    
    @pytest.mark.skipif(not INTEGRATED_DELIVERY_AVAILABLE, reason="Integrated delivery modules not available")
    @pytest.mark.asyncio
    async def test_delivery_retry_logic(self):
        """
        RED TEST: Should retry failed deliveries with exponential backoff
        """
        config = DeliveryConfiguration(
            sender_type="postmark",
            config={"POSTMARK_API_TOKEN": "test-token"},
            service_domain="cellophanemail.com",
            max_retries=3
        )
        
        original_email = EphemeralEmail(
            message_id="retry-test-001",
            from_address="sender@example.com",
            to_addresses=["user@example.com"],
            subject="Test Retry Email",
            text_body="This email will fail initially",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.FORWARD_CLEAN,
            toxicity_score=0.15,
            processed_content="This email will fail initially",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=120
        )
        
        # Mock email sender to fail twice, then succeed
        with patch('cellophanemail.core.email_delivery.factory.EmailSenderFactory.create_sender') as mock_factory:
            mock_sender = AsyncMock()
            mock_sender.send_email.side_effect = [False, False, True]  # Fail, fail, succeed
            mock_factory.return_value = mock_sender
            
            delivery_manager = IntegratedDeliveryManager(config)
            result = await delivery_manager.deliver_email(processing_result, original_email)
            
            # Should eventually succeed after retries
            assert result.success == True
            assert result.attempts == 3
            assert mock_sender.send_email.call_count == 3
    
    @pytest.mark.skipif(not INTEGRATED_DELIVERY_AVAILABLE, reason="Integrated delivery modules not available")
    @pytest.mark.asyncio
    async def test_delivery_complete_failure(self):
        """
        RED TEST: Should handle complete delivery failure after all retries
        """
        config = DeliveryConfiguration(
            sender_type="postmark",
            config={"POSTMARK_API_TOKEN": "test-token"},
            service_domain="cellophanemail.com",
            max_retries=2
        )
        
        original_email = EphemeralEmail(
            message_id="failure-test-001",
            from_address="sender@example.com",
            to_addresses=["user@example.com"],
            subject="Test Failure Email",
            text_body="This email will always fail",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.FORWARD_CLEAN,
            toxicity_score=0.20,
            processed_content="This email will always fail",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=100
        )
        
        # Mock email sender to always fail
        with patch('cellophanemail.core.email_delivery.factory.EmailSenderFactory.create_sender') as mock_factory:
            mock_sender = AsyncMock()
            mock_sender.send_email.return_value = False  # Always fail
            mock_factory.return_value = mock_sender
            
            delivery_manager = IntegratedDeliveryManager(config)
            result = await delivery_manager.deliver_email(processing_result, original_email)
            
            # Should fail after all retries
            assert result.success == False
            assert result.attempts == 2
            assert result.error_message is not None
            assert "failed" in result.error_message.lower()
    
    @pytest.mark.skipif(not INTEGRATED_DELIVERY_AVAILABLE, reason="Integrated delivery modules not available")
    @pytest.mark.asyncio
    async def test_smtp_sender_integration(self):
        """
        RED TEST: Should work with SMTP sender as well as Postmark
        """
        config = DeliveryConfiguration(
            sender_type="smtp",
            config={
                "SMTP_DOMAIN": "cellophanemail.com",
                "EMAIL_USERNAME": "noreply",
                "OUTBOUND_SMTP_HOST": "smtp.example.com",
                "OUTBOUND_SMTP_PORT": "587",
                "EMAIL_PASSWORD": "test-password"
            },
            service_domain="cellophanemail.com"
        )
        
        original_email = EphemeralEmail(
            message_id="smtp-test-001",
            from_address="sender@example.com",
            to_addresses=["user@example.com"],
            subject="SMTP Test Email",
            text_body="Testing SMTP delivery",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.FORWARD_CLEAN,
            toxicity_score=0.08,
            processed_content="Testing SMTP delivery",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=130
        )
        
        # Mock email sender
        with patch('cellophanemail.core.email_delivery.factory.EmailSenderFactory.create_sender') as mock_factory:
            mock_sender = AsyncMock()
            mock_sender.send_email.return_value = True
            mock_factory.return_value = mock_sender
            
            delivery_manager = IntegratedDeliveryManager(config)
            result = await delivery_manager.deliver_email(processing_result, original_email)
        
        # Should work with SMTP sender
        assert result.success == True
        assert result.email_sender_used == "smtp"
        assert result.protection_action == ProtectionAction.FORWARD_CLEAN
    
    @pytest.mark.skipif(not INTEGRATED_DELIVERY_AVAILABLE, reason="Integrated delivery modules not available")
    @pytest.mark.asyncio
    async def test_email_composition_integration(self):
        """
        RED TEST: Should properly integrate with EmailCompositionStrategy
        """
        config = DeliveryConfiguration(
            sender_type="postmark",
            config={"POSTMARK_API_TOKEN": "test-token"},
            service_domain="cellophanemail.com",
            add_transparency_headers=True,
            preserve_threading=True
        )
        
        # Email with threading headers
        original_email = EphemeralEmail(
            message_id="composition-test-001",
            from_address="threaded@example.com",
            to_addresses=["user@example.com"],
            subject="Re: Thread Test",
            text_body="This is part of a thread",
            user_email="user@example.com",
            ttl_seconds=300,
            message_id_header="<thread-456@example.com>",
            in_reply_to="<parent-123@example.com>",
            references="<parent-123@example.com>"
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.REDACT_HARMFUL,
            toxicity_score=0.55,
            processed_content="This is part of a [REDACTED] thread",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=250
        )
        
        # Mock to capture the email details sent
        with patch('cellophanemail.core.email_delivery.factory.EmailSenderFactory.create_sender') as mock_factory:
            mock_sender = AsyncMock()
            mock_sender.send_email.return_value = True
            mock_factory.return_value = mock_sender
            
            delivery_manager = IntegratedDeliveryManager(config)
            result = await delivery_manager.deliver_email(processing_result, original_email)
            
            # Verify email was sent with proper composition
            assert result.success == True
            assert mock_sender.send_email.called
            
            # Get the call arguments to verify proper composition
            call_args = mock_sender.send_email.call_args
            sent_subject = call_args[1]['subject']
            sent_headers = call_args[1]['headers']
            
            # Should have [Filtered] prefix for redacted emails
            assert sent_subject == "[Filtered] Re: Thread Test"
            
            # Should have threading headers preserved
            assert sent_headers["Message-ID"] == "<thread-456@example.com>"
            assert sent_headers["In-Reply-To"] == "<parent-123@example.com>"
            assert sent_headers["References"] == "<parent-123@example.com>"
            
            # Should have transparency headers
            assert sent_headers["X-Protection-Action"] == "redact_harmful"
            assert sent_headers["X-Toxicity-Score"] == "0.55"
            assert sent_headers["X-Original-From"] == "threaded@example.com"
    
    @pytest.mark.skipif(not INTEGRATED_DELIVERY_AVAILABLE, reason="Integrated delivery modules not available")
    def test_enhanced_delivery_result_data_structure(self):
        """
        RED TEST: EnhancedDeliveryResult should have expected structure
        """
        result = EnhancedDeliveryResult(
            success=True,
            attempts=2,
            protection_action=ProtectionAction.FORWARD_CLEAN,
            toxicity_score=0.25,
            error_message=None,
            delivery_time_ms=150,
            email_sender_used="postmark"
        )
        
        assert result.success == True
        assert result.attempts == 2
        assert result.protection_action == ProtectionAction.FORWARD_CLEAN
        assert result.toxicity_score == 0.25
        assert result.error_message is None
        assert result.delivery_time_ms == 150
        assert result.email_sender_used == "postmark"
    
    @pytest.mark.skipif(not INTEGRATED_DELIVERY_AVAILABLE, reason="Integrated delivery modules not available")
    def test_invalid_sender_configuration_error(self):
        """
        RED TEST: Should handle invalid sender configuration gracefully
        """
        # Missing required configuration
        invalid_config = DeliveryConfiguration(
            sender_type="postmark",
            config={"SMTP_DOMAIN": "example.com"},  # Missing POSTMARK_API_TOKEN
            service_domain="cellophanemail.com"
        )
        
        # Should raise appropriate error during initialization
        with pytest.raises(ValueError) as exc_info:
            IntegratedDeliveryManager(invalid_config)
        
        assert "configuration" in str(exc_info.value).lower()
        assert "postmark_api_token" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()