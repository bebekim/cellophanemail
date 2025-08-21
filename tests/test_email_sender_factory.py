"""Tests for EmailSenderFactory."""

import pytest
from cellophanemail.core.email_delivery.factory import EmailSenderFactory
from cellophanemail.core.email_delivery.senders.smtp_sender import SMTPEmailSender
from cellophanemail.core.email_delivery.senders.postmark_sender import PostmarkEmailSender


class TestEmailSenderFactory:
    """Test suite for EmailSenderFactory."""
    
    @pytest.fixture
    def smtp_config(self):
        """SMTP configuration for testing."""
        return {
            'SMTP_DOMAIN': 'cellophanemail.com',
            'EMAIL_USERNAME': 'goldenfermi@gmail.com',
            'EMAIL_PASSWORD': 'test_password',
            'OUTBOUND_SMTP_HOST': 'smtp.gmail.com',
            'OUTBOUND_SMTP_PORT': 587,
            'OUTBOUND_SMTP_USE_TLS': True
        }
    
    @pytest.fixture
    def postmark_config(self):
        """Postmark configuration for testing."""
        return {
            'SMTP_DOMAIN': 'cellophanemail.com',
            'EMAIL_USERNAME': 'goldenfermi@gmail.com',
            'POSTMARK_API_TOKEN': 'test-api-token-123',
            'POSTMARK_FROM_EMAIL': 'noreply@cellophanemail.com'
        }
    
    def test_create_smtp_sender(self, smtp_config):
        """Test creating SMTP sender."""
        sender = EmailSenderFactory.create_sender('smtp', smtp_config)
        
        assert isinstance(sender, SMTPEmailSender)
        assert sender.service_domain == 'cellophanemail.com'
        assert sender.username == 'goldenfermi@gmail.com'
        assert sender.smtp_server == 'smtp.gmail.com'
        assert sender.smtp_port == 587
    
    def test_create_postmark_sender(self, postmark_config):
        """Test creating Postmark sender."""
        sender = EmailSenderFactory.create_sender('postmark', postmark_config)
        
        assert isinstance(sender, PostmarkEmailSender)
        assert sender.service_domain == 'cellophanemail.com'
        assert sender.username == 'goldenfermi@gmail.com'
        assert sender.api_token == 'test-api-token-123'
        assert sender.from_email == 'noreply@cellophanemail.com'
    
    def test_unknown_sender_type(self, smtp_config):
        """Test error handling for unknown sender type."""
        with pytest.raises(ValueError, match="Unknown sender type 'invalid'"):
            EmailSenderFactory.create_sender('invalid', smtp_config)
    
    def test_missing_common_config(self):
        """Test validation of common required configuration."""
        incomplete_config = {
            'SMTP_DOMAIN': 'cellophanemail.com'
            # Missing EMAIL_USERNAME
        }
        
        with pytest.raises(ValueError, match="Missing required configuration fields"):
            EmailSenderFactory.create_sender('smtp', incomplete_config)
    
    def test_missing_smtp_specific_config(self):
        """Test validation of SMTP-specific configuration."""
        incomplete_config = {
            'SMTP_DOMAIN': 'cellophanemail.com',
            'EMAIL_USERNAME': 'goldenfermi@gmail.com'
            # Missing SMTP-specific fields
        }
        
        with pytest.raises(ValueError, match="Missing required smtp configuration fields"):
            EmailSenderFactory.create_sender('smtp', incomplete_config)
    
    def test_missing_postmark_specific_config(self):
        """Test validation of Postmark-specific configuration."""
        incomplete_config = {
            'SMTP_DOMAIN': 'cellophanemail.com',
            'EMAIL_USERNAME': 'goldenfermi@gmail.com'
            # Missing POSTMARK_API_TOKEN
        }
        
        with pytest.raises(ValueError, match="Missing required postmark configuration fields"):
            EmailSenderFactory.create_sender('postmark', incomplete_config)
    
    def test_get_available_senders(self):
        """Test getting list of available senders."""
        available = EmailSenderFactory.get_available_senders()
        
        assert 'smtp' in available
        assert 'postmark' in available
        assert len(available) >= 2
    
    def test_register_new_sender(self, smtp_config):
        """Test registering a new sender type."""
        # Create a mock sender class
        class MockEmailSender(SMTPEmailSender):
            pass
        
        # Register the new sender
        EmailSenderFactory.register_sender('mock', MockEmailSender)
        
        # Verify it was registered
        available = EmailSenderFactory.get_available_senders()
        assert 'mock' in available
        
        # Verify we can create it
        sender = EmailSenderFactory.create_sender('mock', smtp_config)
        assert isinstance(sender, MockEmailSender)
    
    def test_register_invalid_sender(self):
        """Test error when registering non-BaseEmailSender class."""
        class InvalidSender:
            pass
        
        with pytest.raises(ValueError, match="must inherit from BaseEmailSender"):
            EmailSenderFactory.register_sender('invalid', InvalidSender)
