"""Tests for PostmarkEmailSender - Postmark API implementation of BaseEmailSender."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from cellophanemail.core.email_delivery.senders.postmark_sender import PostmarkEmailSender


class TestPostmarkEmailSender:
    """Test suite for PostmarkEmailSender."""
    
    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return {
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {},
            'EMAIL_USERNAME': 'goldenfermi@gmail.com',
            'POSTMARK_API_TOKEN': 'test-api-token-123',
            'POSTMARK_FROM_EMAIL': 'noreply@cellophanemail.com'
        }
    
    @pytest.fixture
    def postmark_sender(self, config):
        """Create PostmarkEmailSender instance."""
        return PostmarkEmailSender(config)
    
    def test_initialization(self, config):
        """Test PostmarkEmailSender initializes with correct configuration."""
        sender = PostmarkEmailSender(config)
        
        # Should inherit from BaseEmailSender
        assert sender.service_domain == 'cellophanemail.com'
        assert sender.username == 'goldenfermi@gmail.com'
        
        # Should have Postmark-specific config
        assert sender.api_token == 'test-api-token-123'
        assert sender.from_email == 'noreply@cellophanemail.com'
        assert sender.api_url == 'https://api.postmarkapp.com/email'
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, postmark_sender):
        """Test successful email sending via Postmark API."""
        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'MessageID': 'test-message-id',
            'To': 'goldenfermi@gmail.com',
            'SubmittedAt': '2025-08-09T10:00:00Z'
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            
            result = await postmark_sender.send_email(
                to_address='goldenfermi@gmail.com',
                subject='Test Subject',
                content='Test content',
                headers={
                    'From': 'CellophoneMail Shield <noreply@cellophanemail.com>',
                    'Message-ID': '<test123@cellophanemail.com>',
                    'In-Reply-To': '<original@gmail.com>',
                    'References': '<original@gmail.com>',
                    'Reply-To': 'thread-abc123@cellophanemail.com'
                }
            )
            
            assert result is True
            
            # Verify Postmark API was called correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            
            # Check API endpoint
            assert call_args[0][0] == 'https://api.postmarkapp.com/email'
            
            # Check request headers
            request_headers = call_args[1]['headers']
            assert request_headers['Accept'] == 'application/json'
            assert request_headers['Content-Type'] == 'application/json'
            assert request_headers['X-Postmark-Server-Token'] == 'test-api-token-123'
            
            # Check request payload
            payload = call_args[1]['json']
            assert payload['From'] == 'CellophoneMail Shield <noreply@cellophanemail.com>'
            assert payload['To'] == 'goldenfermi@gmail.com'
            assert payload['Subject'] == 'Test Subject'
            assert payload['TextBody'] == 'Test content'
            assert payload['MessageID'] == '<test123@cellophanemail.com>'
            assert payload['InReplyTo'] == '<original@gmail.com>'
            assert payload['References'] == '<original@gmail.com>'
            assert payload['ReplyTo'] == 'thread-abc123@cellophanemail.com'
    
    @pytest.mark.asyncio
    async def test_send_email_api_failure(self, postmark_sender):
        """Test email sending failure handling - API error."""
        # Mock httpx.AsyncClient with error response
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            'ErrorCode': 300,
            'Message': 'Invalid email request'
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            
            result = await postmark_sender.send_email(
                to_address='invalid@example.com',
                subject='Test Subject',
                content='Test content',
                headers={'From': 'CellophoneMail Shield <noreply@cellophanemail.com>'}
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_email_network_failure(self, postmark_sender):
        """Test email sending failure handling - network exception."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Network timeout")
            
            result = await postmark_sender.send_email(
                to_address='goldenfermi@gmail.com',
                subject='Test Subject',
                content='Test content',
                headers={'From': 'CellophoneMail Shield <noreply@cellophanemail.com>'}
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_filtered_email_integration_safe(self, postmark_sender):
        """Test full integration with BaseEmailSender for SAFE email."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'MessageID': 'test-id'}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            
            ai_result = {'ai_classification': 'SAFE'}
            original_email_data = {
                'original_subject': 'Hello',
                'original_sender': 'friend@example.com',
                'original_body': 'This is a safe email',
                'message_id': '<original123@example.com>'
            }
            
            result = await postmark_sender.send_filtered_email(
                recipient_shield_address='yh.kim@cellophanemail.com',
                ai_result=ai_result,
                original_email_data=original_email_data
            )
            
            assert result is True
            
            # Verify the email was sent with correct content
            mock_client.post.assert_called_once()
            payload = mock_client.post.call_args[1]['json']
            
            assert payload['To'] == 'goldenfermi@gmail.com'
            assert payload['Subject'] == 'Hello'
            assert 'This is a safe email' in payload['TextBody']
            assert 'Protected by CellophoneMail Email Protection Service' in payload['TextBody']
    
    @pytest.mark.asyncio
    async def test_send_filtered_email_integration_harmful(self, postmark_sender):
        """Test full integration with BaseEmailSender for HARMFUL email."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'MessageID': 'test-id'}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            
            ai_result = {
                'ai_classification': 'ABUSIVE',
                'horsemen_detected': ['criticism', 'contempt']
            }
            original_email_data = {
                'original_subject': 'Test Email',
                'original_sender': 'abusiveparent@gmail.com',
                'original_body': 'Harmful content here',
                'message_id': '<original456@gmail.com>'
            }
            
            result = await postmark_sender.send_filtered_email(
                recipient_shield_address='yh.kim@cellophanemail.com',
                ai_result=ai_result,
                original_email_data=original_email_data
            )
            
            assert result is True
            
            # Verify the filtered email was sent
            mock_client.post.assert_called_once()
            payload = mock_client.post.call_args[1]['json']
            
            assert payload['To'] == 'goldenfermi@gmail.com'
            assert payload['Subject'] == '[Filtered] Test Email'
            text_body = payload['TextBody']
            assert '⚠️ Email filtered by CellophoneMail' in text_body
            assert 'Original sender: abusiveparent@gmail.com' in text_body
            assert 'Detected: criticism, contempt' in text_body
            assert 'Classification: ABUSIVE' in text_body