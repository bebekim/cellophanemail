"""Tests for SMTPEmailSender - SMTP implementation of BaseEmailSender."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from cellophanemail.core.email_delivery.senders.smtp_sender import SMTPEmailSender


class TestSMTPEmailSender:
    """Test suite for SMTPEmailSender."""
    
    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return {
            'SMTP_DOMAIN': 'cellophanemail.com',
            'SERVICE_CONSTANTS': {},
            'EMAIL_USERNAME': 'goldenfermi@gmail.com',
            'EMAIL_PASSWORD': 'test_password',
            'OUTBOUND_SMTP_HOST': 'smtp.gmail.com',
            'OUTBOUND_SMTP_PORT': 587,
            'OUTBOUND_SMTP_USE_TLS': True
        }
    
    @pytest.fixture
    def smtp_sender(self, config):
        """Create SMTPEmailSender instance."""
        return SMTPEmailSender(config)
    
    def test_initialization(self, config):
        """Test SMTPEmailSender initializes with correct configuration."""
        sender = SMTPEmailSender(config)
        
        # Should inherit from BaseEmailSender
        assert sender.service_domain == 'cellophanemail.com'
        assert sender.username == 'goldenfermi@gmail.com'
        
        # Should have SMTP-specific config
        assert sender.smtp_server == 'smtp.gmail.com'
        assert sender.smtp_port == 587
        assert sender.use_tls is True
        assert sender.password == 'test_password'
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, smtp_sender):
        """Test successful email sending via SMTP."""
        # Mock aiosmtplib.send
        with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (None, "250 OK")
            
            result = await smtp_sender.send_email(
                to_address='goldenfermi@gmail.com',
                subject='Test Subject',
                content='Test content',
                headers={
                    'From': 'CellophoneMail Shield <noreply@cellophanemail.com>',
                    'Message-ID': '<test123@cellophanemail.com>',
                    'In-Reply-To': '<original@gmail.com>',
                    'References': '<original@gmail.com>'
                }
            )
            
            assert result is True
            
            # Verify aiosmtplib.send was called correctly
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            
            # Check the message object
            msg = call_args[0][0]
            assert msg['To'] == 'goldenfermi@gmail.com'
            assert msg['Subject'] == 'Test Subject'
            assert msg['From'] == 'CellophoneMail Shield <noreply@cellophanemail.com>'
            assert msg['Message-ID'] == '<test123@cellophanemail.com>'
            assert msg['In-Reply-To'] == '<original@gmail.com>'
            assert msg['References'] == '<original@gmail.com>'
            assert msg.get_payload() == 'Test content'
            
            # Check SMTP connection parameters
            assert call_args[1]['hostname'] == 'smtp.gmail.com'
            assert call_args[1]['port'] == 587
            assert call_args[1]['username'] == 'goldenfermi@gmail.com'
            assert call_args[1]['password'] == 'test_password'
    
    @pytest.mark.asyncio
    async def test_send_email_failure(self, smtp_sender):
        """Test email sending failure handling."""
        # Mock aiosmtplib.send to raise an exception
        with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("SMTP connection failed")
            
            result = await smtp_sender.send_email(
                to_address='goldenfermi@gmail.com',
                subject='Test Subject',
                content='Test content',
                headers={'From': 'CellophoneMail Shield <noreply@cellophanemail.com>'}
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_filtered_email_integration_safe(self, smtp_sender):
        """Test full integration with BaseEmailSender for SAFE email."""
        with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (None, "250 OK")
            
            ai_result = {'ai_classification': 'SAFE'}
            original_email_data = {
                'original_subject': 'Hello',
                'original_sender': 'friend@example.com',
                'original_body': 'This is a safe email',
                'message_id': '<original123@example.com>'
            }
            
            result = await smtp_sender.send_filtered_email(
                recipient_shield_address='yh.kim@cellophanemail.com',
                ai_result=ai_result,
                original_email_data=original_email_data
            )
            
            assert result is True
            
            # Verify the email was sent with correct content
            mock_send.assert_called_once()
            msg = mock_send.call_args[0][0]
            
            assert msg['To'] == 'goldenfermi@gmail.com'
            assert msg['Subject'] == 'Hello'
            assert 'This is a safe email' in msg.get_payload()
            assert 'Protected by CellophoneMail Email Protection Service' in msg.get_payload()
    
    @pytest.mark.asyncio
    async def test_send_filtered_email_integration_harmful(self, smtp_sender):
        """Test full integration with BaseEmailSender for HARMFUL email."""
        with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (None, "250 OK")
            
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
            
            result = await smtp_sender.send_filtered_email(
                recipient_shield_address='yh.kim@cellophanemail.com',
                ai_result=ai_result,
                original_email_data=original_email_data
            )
            
            assert result is True
            
            # Verify the filtered email was sent
            mock_send.assert_called_once()
            msg = mock_send.call_args[0][0]
            
            assert msg['To'] == 'goldenfermi@gmail.com'
            assert msg['Subject'] == '[Filtered] Test Email'
            payload = msg.get_payload()
            # Content might be base64 encoded, so decode if needed
            if isinstance(payload, str) and '\n' in payload and not '⚠️' in payload:
                import base64
                try:
                    payload = base64.b64decode(payload.replace('\n', '')).decode('utf-8')
                except:
                    pass  # If decoding fails, use original payload
                    
            assert '⚠️ Email filtered by CellophoneMail' in payload
            assert 'Original sender: abusiveparent@gmail.com' in payload
            assert 'Detected: criticism, contempt' in payload
            assert 'Classification: ABUSIVE' in payload
