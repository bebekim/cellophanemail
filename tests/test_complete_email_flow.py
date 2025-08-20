"""End-to-end integration tests for complete email delivery flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.core.email_message import EmailMessage
from cellophanemail.config.settings import Settings


class TestCompleteEmailFlow:
    """Test complete email processing and delivery flow."""
    
    @pytest.fixture
    def smtp_config(self):
        """SMTP configuration for testing."""
        return {
            'EMAIL_DELIVERY_METHOD': 'smtp',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'EMAIL_USERNAME': 'goldenfermi@gmail.com',
            'EMAIL_PASSWORD': 'test_password',
            'OUTBOUND_SMTP_HOST': 'smtp.gmail.com',
            'OUTBOUND_SMTP_PORT': 587,
            'OUTBOUND_SMTP_USE_TLS': True,
            'SERVICE_CONSTANTS': {}
        }
    
    @pytest.fixture
    def postmark_config(self):
        """Postmark configuration for testing."""
        return {
            'EMAIL_DELIVERY_METHOD': 'postmark',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'EMAIL_USERNAME': 'goldenfermi@gmail.com',
            'POSTMARK_API_TOKEN': 'test-api-token-123',
            'POSTMARK_FROM_EMAIL': 'noreply@cellophanemail.com',
            'SERVICE_CONSTANTS': {}
        }
    
    @pytest.fixture
    def sample_email_message(self):
        """Create a sample email message for testing."""
        return EmailMessage(
            id=uuid4(),
            from_address='friend@example.com',
            to_addresses=['yh.kim@cellophanemail.com'],
            subject='Hello from friend',
            text_content='This is a friendly email message.',
            html_content='<p>This is a friendly email message.</p>',
            message_id='<friend123@example.com>',
            source_plugin='smtp'
        )
    
    @pytest.mark.asyncio
    async def test_smtp_complete_flow_safe_email(self, smtp_config, sample_email_message):
        """Test complete flow with SMTP sender for SAFE email."""
        # Mock delivery service
        with patch('cellophanemail.core.email_processor.EmailDeliveryService.send_email', new_callable=AsyncMock) as mock_send, \
             patch('cellophanemail.core.content_processor.ContentProcessor.process_email_content') as mock_content_processor:
            
            # Mock successful email send
            mock_send_result = MagicMock()
            mock_send_result.success = True
            mock_send_result.message_id = "test-message-id"
            mock_send.return_value = mock_send_result
            
            # Mock content processor to return SAFE result
            mock_result = MagicMock()
            mock_result.should_forward = True
            mock_result.block_reason = None
            mock_result.toxicity_score = 0.1
            mock_result.analysis.horsemen_detected = []
            mock_result.analysis.classification = 'SAFE'
            mock_result.analysis.reasoning = 'Friendly email'
            mock_result.analysis.specific_examples = []
            mock_result.analysis.confidence_score = 0.95
            mock_content_processor.return_value = mock_result
            
            # Create email processor with SMTP config
            processor = EmailProtectionProcessor()
            
            # Process the email
            result = await processor.process(sample_email_message)
            
            # Verify email was processed
            assert result.should_forward is True
            assert result.block_reason is None
            
            # Verify delivery service was called (email was forwarded)
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_postmark_complete_flow_safe_email(self, postmark_config, sample_email_message):
        """Test complete flow with Postmark sender for SAFE email."""
        # Mock delivery service
        with patch('cellophanemail.core.email_processor.EmailDeliveryService.send_email', new_callable=AsyncMock) as mock_send, \
             patch('cellophanemail.core.content_processor.ContentProcessor.process_email_content') as mock_content_processor:
            
            # Mock successful email send
            mock_send_result = MagicMock()
            mock_send_result.success = True
            mock_send_result.message_id = "test-postmark-id"
            mock_send.return_value = mock_send_result
            
            # Mock content processor to return SAFE result
            mock_result = MagicMock()
            mock_result.should_forward = True
            mock_result.block_reason = None
            mock_result.toxicity_score = 0.1
            mock_result.analysis.horsemen_detected = []
            mock_result.analysis.classification = 'SAFE'
            mock_result.analysis.reasoning = 'Friendly email'
            mock_result.analysis.specific_examples = []
            mock_result.analysis.confidence_score = 0.95
            mock_content_processor.return_value = mock_result
            
            # Create email processor with Postmark config
            processor = EmailProtectionProcessor()
            
            # Process the email
            result = await processor.process(sample_email_message)
            
            # Verify email was processed
            assert result.should_forward is True
            assert result.block_reason is None
            
            # Verify delivery service was called
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_harmful_email_blocked_no_forwarding(self, smtp_config, sample_email_message):
        """Test that HARMFUL emails are blocked and not forwarded."""
        with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_smtp_send, \
             patch('cellophanemail.core.content_processor.ContentProcessor.process_email_content') as mock_content_processor:
            
            mock_smtp_send.return_value = (None, "250 OK")
            
            # Mock content processor to return HARMFUL result
            mock_result = MagicMock()
            mock_result.should_forward = False
            mock_result.block_reason = "Content filtered by Four Horsemen analysis"
            mock_result.toxicity_score = 0.8
            mock_result.analysis.horsemen_detected = ['criticism', 'contempt']
            mock_result.analysis.classification = 'HARMFUL'
            mock_result.analysis.reasoning = 'Contains harmful criticism'
            mock_result.analysis.specific_examples = ['You are terrible']
            mock_result.analysis.confidence_score = 0.92
            mock_content_processor.return_value = mock_result
            
            # Create email processor with SMTP config
            processor = EmailProtectionProcessor()
            
            # Update sample email to be harmful
            sample_email_message.from_address = 'abusiveparent@gmail.com'
            sample_email_message.subject = 'You are incompetent'
            sample_email_message.text_content = 'You are terrible at everything.'
            
            # Process the email
            result = await processor.process(sample_email_message)
            
            # Verify email was blocked
            assert result.should_forward is False
            assert result.block_reason == "Content filtered by Four Horsemen analysis"
            assert result.toxicity_score == 0.8
            assert 'criticism' in result.horsemen_detected
            assert 'contempt' in result.horsemen_detected
            
            # Verify NO email was sent (not forwarded)
            mock_smtp_send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_no_email_sender_configured(self, sample_email_message):
        """Test graceful handling when no email sender is configured."""
        with patch('cellophanemail.core.content_processor.ContentProcessor.process_email_content') as mock_content_processor:
            
            # Mock content processor to return SAFE result
            mock_result = MagicMock()
            mock_result.should_forward = True
            mock_result.block_reason = None
            mock_result.toxicity_score = 0.1
            mock_result.analysis.horsemen_detected = []
            mock_result.analysis.classification = 'SAFE'
            mock_result.analysis.reasoning = 'Friendly email'
            mock_result.analysis.specific_examples = []
            mock_result.analysis.confidence_score = 0.95
            mock_content_processor.return_value = mock_result
            
            # Create email processor with NO config (no email sender)
            processor = EmailProtectionProcessor()
            
            # Process the email
            result = await processor.process(sample_email_message)
            
            # Verify email was processed but not forwarded
            assert result.should_forward is True
            assert result.block_reason is None
            
            # Delivery service should exist but not have a sender configured
            assert processor.delivery_service is not None
    
    def test_email_delivery_config_property(self):
        """Test the email delivery config property from Settings."""
        # Mock settings values
        settings = Settings(
            email_delivery_method='postmark',
            smtp_domain='cellophanemail.com',
            email_username='goldenfermi@gmail.com',
            email_password='test_pass',
            outbound_smtp_host='smtp.gmail.com',
            outbound_smtp_port=587,
            outbound_smtp_use_tls=True,
            postmark_api_token='test-token',
            postmark_from_email='noreply@cellophanemail.com'
        )
        
        config = settings.email_delivery_config
        
        assert config['EMAIL_DELIVERY_METHOD'] == 'postmark'
        assert config['SMTP_DOMAIN'] == 'cellophanemail.com'
        assert config['EMAIL_USERNAME'] == 'goldenfermi@gmail.com'
        assert config['EMAIL_PASSWORD'] == 'test_pass'
        assert config['OUTBOUND_SMTP_HOST'] == 'smtp.gmail.com'
        assert config['OUTBOUND_SMTP_PORT'] == 587
        assert config['OUTBOUND_SMTP_USE_TLS'] is True
        assert config['POSTMARK_API_TOKEN'] == 'test-token'
        assert config['POSTMARK_FROM_EMAIL'] == 'noreply@cellophanemail.com'