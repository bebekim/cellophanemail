"""Unit tests for EmailMessage.from_postmark_webhook() method."""

import pytest
from datetime import datetime
from cellophanemail.core.email_message import EmailMessage


class TestEmailMessageFromPostmarkWebhook:
    """Test cases for creating EmailMessage from Postmark webhook data."""
    
    def test_from_postmark_webhook_method_exists(self):
        """Test that EmailMessage has from_postmark_webhook class method."""
        # RED: This test will fail because the method doesn't exist yet
        assert hasattr(EmailMessage, 'from_postmark_webhook')
        assert callable(getattr(EmailMessage, 'from_postmark_webhook'))
    
    def test_basic_postmark_webhook_parsing(self):
        """Test basic Postmark webhook data parsing."""
        webhook_data = {
            "From": "sender@example.com",
            "To": "a1b2c3d4e5f6789012345678901234567@cellophanemail.com",
            "Subject": "Test email",
            "TextBody": "Plain text content",
            "HtmlBody": "<p>HTML content</p>",
            "MessageID": "msg-123"
        }
        
        # RED: This will fail because method doesn't exist
        email_message = EmailMessage.from_postmark_webhook(webhook_data)
        
        assert email_message.from_address == "sender@example.com"
        assert email_message.to_addresses == ["a1b2c3d4e5f6789012345678901234567@cellophanemail.com"]
        assert email_message.subject == "Test email"
        assert email_message.text_content == "Plain text content"
        assert email_message.html_content == "<p>HTML content</p>"
        assert email_message.message_id == "msg-123"
        assert email_message.source_plugin == "postmark"
    
    def test_multiple_recipients_parsing(self):
        """Test parsing multiple recipients in To field."""
        webhook_data = {
            "From": "sender@example.com",
            "To": "user1@cellophanemail.com, user2@cellophanemail.com",
            "Subject": "Multiple recipients",
            "TextBody": "Text content"
        }
        
        # RED: This will fail
        email_message = EmailMessage.from_postmark_webhook(webhook_data)
        
        assert len(email_message.to_addresses) == 2
        assert "user1@cellophanemail.com" in email_message.to_addresses
        assert "user2@cellophanemail.com" in email_message.to_addresses
    
    def test_headers_parsing(self):
        """Test parsing Postmark headers format."""
        webhook_data = {
            "From": "sender@example.com",
            "To": "user@cellophanemail.com",
            "Subject": "With headers",
            "Headers": [
                {"Name": "X-Custom-Header", "Value": "custom-value"},
                {"Name": "X-Priority", "Value": "1"}
            ]
        }
        
        # RED: This will fail
        email_message = EmailMessage.from_postmark_webhook(webhook_data)
        
        assert email_message.headers["X-Custom-Header"] == "custom-value"
        assert email_message.headers["X-Priority"] == "1"
    
    def test_attachments_parsing(self):
        """Test parsing Postmark attachments format."""
        webhook_data = {
            "From": "sender@example.com",
            "To": "user@cellophanemail.com",
            "Subject": "With attachments",
            "Attachments": [
                {
                    "Name": "document.pdf",
                    "ContentType": "application/pdf",
                    "ContentLength": 1024,
                    "Content": "base64encodedcontent"
                }
            ]
        }
        
        # RED: This will fail
        email_message = EmailMessage.from_postmark_webhook(webhook_data)
        
        assert len(email_message.attachments) == 1
        attachment = email_message.attachments[0]
        assert attachment["name"] == "document.pdf"
        assert attachment["content_type"] == "application/pdf"
        assert attachment["content_length"] == 1024
        assert attachment["content"] == "base64encodedcontent"
    
    def test_missing_optional_fields(self):
        """Test handling of missing optional fields."""
        webhook_data = {
            "From": "sender@example.com",
            "To": "user@cellophanemail.com",
            "Subject": "Minimal data"
            # TextBody, HtmlBody, Headers, Attachments are missing
        }
        
        # RED: This will fail
        email_message = EmailMessage.from_postmark_webhook(webhook_data)
        
        assert email_message.text_content == ""
        assert email_message.html_content == ""
        assert email_message.headers == {}
        assert email_message.attachments == []
    
    def test_received_at_timestamp(self):
        """Test that received_at is set to current datetime."""
        webhook_data = {
            "From": "sender@example.com",
            "To": "user@cellophanemail.com",
            "Subject": "Timestamp test"
        }
        
        before_time = datetime.now()
        
        # RED: This will fail
        email_message = EmailMessage.from_postmark_webhook(webhook_data)
        
        after_time = datetime.now()
        
        assert before_time <= email_message.received_at <= after_time
