"""End-to-end integration tests for complete email delivery flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from cellophanemail.core.email_processor import EmailProcessor
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
        # Mock SMTP sending
        with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_smtp_send, \
             patch('cellophanemail.core.content_processor.ContentProcessor.process_email_content') as mock_content_processor:
            
            mock_smtp_send.return_value = (None, "250 OK")
            
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
            processor = EmailProcessor(smtp_config)
            
            # Process the email
            result = await processor.process(sample_email_message)
            
            # Verify email was processed
            assert result.should_forward is True
            assert result.block_reason is None
            
            # Verify SMTP was called (email was forwarded)
            mock_smtp_send.assert_called_once()
            
            # Verify email content
            sent_message = mock_smtp_send.call_args[0][0]
            assert sent_message['To'] == 'goldenfermi@gmail.com'
            assert sent_message['Subject'] == 'Hello from friend'
            assert 'This is a friendly email message.' in sent_message.get_payload()
            assert 'Protected by CellophoneMail Email Protection Service' in sent_message.get_payload()
            assert sent_message['From'] == 'CellophoneMail Shield <noreply@cellophanemail.com>'
    
    @pytest.mark.asyncio
    async def test_postmark_complete_flow_safe_email(self, postmark_config, sample_email_message):
        """Test complete flow with Postmark sender for SAFE email."""
        # Mock Postmark API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'MessageID': 'test-id'}
        
        with patch('httpx.AsyncClient') as mock_client_class, \
             patch('cellophanemail.core.content_processor.ContentProcessor.process_email_content') as mock_content_processor:
            
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            
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
            processor = EmailProcessor(postmark_config)
            
            # Process the email
            result = await processor.process(sample_email_message)
            
            # Verify email was processed
            assert result.should_forward is True
            assert result.block_reason is None
            
            # Verify Postmark API was called
            mock_client.post.assert_called_once()
            
            # Verify API call details
            call_args = mock_client.post.call_args
            assert call_args[0][0] == 'https://api.postmarkapp.com/email'
            
            payload = call_args[1]['json']
            assert payload['To'] == 'goldenfermi@gmail.com'
            assert payload['Subject'] == 'Hello from friend'
            assert 'This is a friendly email message.' in payload['TextBody']
            assert 'Protected by CellophoneMail Email Protection Service' in payload['TextBody']
            assert payload['From'] == 'noreply@cellophanemail.com'
    
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
            processor = EmailProcessor(smtp_config)
            
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
            processor = EmailProcessor()
            
            # Process the email
            result = await processor.process(sample_email_message)
            
            # Verify email was processed but not forwarded
            assert result.should_forward is True
            assert result.block_reason is None
            
            # Email sender should be None
            assert processor.email_sender is None
    
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