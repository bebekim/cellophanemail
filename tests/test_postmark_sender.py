"""Test PostmarkEmailSender class that replaces SMTP with Postmark API."""

import pytest
from unittest.mock import Mock, patch

# Mock flask before importing PostmarkEmailSender
with patch.dict('sys.modules', {'flask': Mock()}):
    from src.cellophanemail.core.postmark_sender import PostmarkEmailSender


class TestPostmarkEmailSender:
    """Test class for PostmarkEmailSender functionality."""
    
    def test_postmark_sender_initialization(self):
        """Test that PostmarkEmailSender can be instantiated with basic configuration."""
        # Arrange - create mock app with Postmark configuration
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'test@example.com'
        }
        
        # Act & Assert - this should succeed once we implement the class
        sender = PostmarkEmailSender(app=mock_app)
        
        # Verify basic attributes are set
        assert sender.api_token == 'test-token'
        assert sender.service_domain == 'cellophanemail.com'
        assert sender.username == 'test@example.com'
    
    def test_extract_email_from_shield_valid_address(self):
        """Test extracting real email from valid shield address."""
        # Arrange
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'real_user@gmail.com'
        }
        sender = PostmarkEmailSender(app=mock_app)
        
        # Act
        result = sender.extract_email_from_shield('shield@cellophanemail.com')
        
        # Assert
        assert result == 'real_user@gmail.com'
    
    def test_extract_email_from_shield_invalid_address(self):
        """Test extracting email from invalid shield address returns None."""
        # Arrange
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'real_user@gmail.com'
        }
        sender = PostmarkEmailSender(app=mock_app)
        
        # Act & Assert
        assert sender.extract_email_from_shield('invalid@otherdomain.com') is None
        assert sender.extract_email_from_shield('invalid-email') is None
        assert sender.extract_email_from_shield(None) is None
        assert sender.extract_email_from_shield('') is None
    
    def test_build_threading_headers(self):
        """Test building threading headers for email replies."""
        # Arrange
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'test@gmail.com'
        }
        sender = PostmarkEmailSender(app=mock_app)
        
        original_email = {
            'message_id': '<original123@sender.com>',
            'subject': 'Original Subject',
            'from': 'sender@example.com'
        }
        
        # Act
        headers = sender.build_threading_headers(original_email)
        
        # Assert
        assert 'Message-ID' in headers
        assert headers['Message-ID'].endswith('@cellophanemail.com>')
        assert headers['In-Reply-To'] == '<original123@sender.com>'
        assert headers['References'] == '<original123@sender.com>'
    
    def test_build_anti_spoofing_headers_basic(self):
        """Test building basic anti-spoofing headers."""
        # Arrange
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'test@gmail.com'
        }
        sender = PostmarkEmailSender(app=mock_app)
        
        # Act
        headers = sender.build_anti_spoofing_headers('sender@example.com')
        
        # Assert
        assert headers['From'] == 'CellophoneMail Shield <noreply@cellophanemail.com>'
        assert 'Reply-To' not in headers  # No thread_id provided
    
    def test_build_anti_spoofing_headers_with_thread_id(self):
        """Test building anti-spoofing headers with thread ID for replies."""
        # Arrange
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'test@gmail.com'
        }
        sender = PostmarkEmailSender(app=mock_app)
        
        # Act
        headers = sender.build_anti_spoofing_headers('sender@example.com', thread_id='abc123')
        
        # Assert
        assert headers['From'] == 'CellophoneMail Shield <noreply@cellophanemail.com>'
        assert headers['Reply-To'] == 'thread-abc123@cellophanemail.com'
    
    @pytest.mark.asyncio
    @patch('postmark.SendingAPIApi')
    async def test_send_filtered_email_safe_classification(self, mock_sending_api):
        """Test sending email with SAFE classification - should pass through with footer."""
        # Arrange - Mock Postmark API
        mock_api_instance = Mock()
        mock_sending_api.return_value = mock_api_instance
        mock_api_instance.send_email.return_value = Mock(message_id='test-message-id', to=['real_user@gmail.com'])
        
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'real_user@gmail.com'
        }
        mock_app.logger = Mock()  # Mock logger
        
        sender = PostmarkEmailSender(app=mock_app)
        
        ai_result = {
            'ai_classification': 'SAFE'
        }
        
        original_email_data = {
            'original_subject': 'Test Subject',
            'original_sender': 'sender@example.com',
            'original_body': 'This is a safe message',
            'message_id': '<test123@example.com>'
        }
        
        # Act
        await sender.send_filtered_email('shield@cellophanemail.com', ai_result, original_email_data)
        
        # Assert - verify Postmark API was called
        mock_api_instance.send_email.assert_called_once()
        
        # Get the actual call arguments
        call_args = mock_api_instance.send_email.call_args[1]
        email_request = call_args['send_email_request']
        assert email_request.to == 'real_user@gmail.com'
        assert email_request.subject == 'Test Subject'
        assert 'This is a safe message' in email_request.text_body
        assert 'Protected by CellophoneMail' in email_request.text_body
    
    @pytest.mark.asyncio
    @patch('postmark.SendingAPIApi')
    async def test_send_filtered_email_harmful_classification(self, mock_sending_api):
        """Test sending email with HARMFUL classification - should send filtered warning."""
        # Arrange - Mock Postmark API
        mock_api_instance = Mock()
        mock_sending_api.return_value = mock_api_instance
        mock_api_instance.send_email.return_value = Mock(message_id='test-message-id')
        
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'real_user@gmail.com'
        }
        
        sender = PostmarkEmailSender(app=mock_app)
        
        ai_result = {
            'ai_classification': 'HARMFUL',
            'horsemen_detected': ['spam', 'phishing']
        }
        
        original_email_data = {
            'original_subject': 'Win Money Now!',
            'original_sender': 'scammer@badsite.com',
            'original_body': 'Click here to win $1000',
            'message_id': '<spam123@badsite.com>'
        }
        
        # Act
        await sender.send_filtered_email('shield@cellophanemail.com', ai_result, original_email_data)
        
        # Assert - verify Postmark API was called with filtered content
        mock_api_instance.send_email.assert_called_once()
        
        # Get the actual call arguments
        call_args = mock_api_instance.send_email.call_args[1]
        email_request = call_args['send_email_request']
        assert email_request.to == 'real_user@gmail.com'
        assert email_request.subject == '[Filtered] Win Money Now!'
        assert '⚠️ Email filtered by CellophoneMail' in email_request.text_body
        assert 'scammer@badsite.com' in email_request.text_body
        assert 'spam, phishing' in email_request.text_body
        assert 'HARMFUL' in email_request.text_body
    
    @pytest.mark.asyncio
    @patch('postmark.SendingAPIApi')
    async def test_send_filtered_email_handles_api_errors_gracefully(self, mock_sending_api):
        """Test that API errors are logged but don't crash the method."""
        # Arrange - Mock Postmark API to raise an exception
        mock_api_instance = Mock()
        mock_sending_api.return_value = mock_api_instance
        mock_api_instance.send_email.side_effect = Exception("API Error")
        
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'real_user@gmail.com'
        }
        
        sender = PostmarkEmailSender(app=mock_app)
        
        ai_result = {'ai_classification': 'SAFE'}
        original_email_data = {
            'original_subject': 'Test Subject',
            'original_sender': 'sender@example.com',
            'original_body': 'Test message',
            'message_id': '<test123@example.com>'
        }
        
        # Act - this should not raise an exception
        await sender.send_filtered_email('shield@cellophanemail.com', ai_result, original_email_data)
        
        # Assert - verify the API was called despite the error
        mock_api_instance.send_email.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('postmark.SendingAPIApi')
    async def test_send_filtered_email_includes_proper_headers(self, mock_sending_api):
        """Test that threading and anti-spoofing headers are included in email."""
        # Arrange - Mock Postmark API
        mock_api_instance = Mock()
        mock_sending_api.return_value = mock_api_instance
        mock_api_instance.send_email.return_value = Mock(message_id='test-message-id')
        
        mock_app = Mock()
        mock_app.config = {
            'POSTMARK_API_TOKEN': 'test-token',
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {'test': 'value'},
            'EMAIL_USERNAME': 'real_user@gmail.com'
        }
        
        sender = PostmarkEmailSender(app=mock_app)
        
        ai_result = {'ai_classification': 'SAFE'}
        original_email_data = {
            'original_subject': 'Test Subject',
            'original_sender': 'sender@example.com',
            'original_body': 'Test message',
            'message_id': '<original123@example.com>'
        }
        
        # Act
        await sender.send_filtered_email('shield@cellophanemail.com', ai_result, original_email_data)
        
        # Assert - verify headers are included
        mock_api_instance.send_email.assert_called_once()
        call_args = mock_api_instance.send_email.call_args[1]
        email_request = call_args['send_email_request']
        
        # Verify From header is set properly
        assert email_request._from == 'CellophoneMail Shield <noreply@cellophanemail.com>'
        
        # Verify custom headers are included
        assert hasattr(email_request, 'headers')
        assert email_request.headers is not None
        
        # Check for threading headers
        header_dict = {h['Name']: h['Value'] for h in email_request.headers}
        assert 'Message-ID' in header_dict
        assert header_dict['Message-ID'].endswith('@cellophanemail.com>')
        assert header_dict['In-Reply-To'] == '<original123@example.com>'
        assert header_dict['References'] == '<original123@example.com>'
        assert 'Reply-To' in header_dict  # Should have Reply-To with thread ID