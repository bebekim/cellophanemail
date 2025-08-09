"""Tests for BaseEmailSender shared methods."""

import pytest
from unittest.mock import Mock
from src.cellophanemail.core.email_delivery.base import BaseEmailSender


class TestBaseEmailSender:
    """Test shared methods in BaseEmailSender abstract class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a concrete implementation for testing abstract methods
        class TestableEmailSender(BaseEmailSender):
            async def send_email(self, msg, recipient):
                """Concrete implementation for testing."""
                return "test_result"
        
        # Initialize with test configuration
        self.sender = TestableEmailSender(
            service_domain='cellophanemail.com',
            username='goldenfermi@gmail.com'
        )
    
    def test_extract_email_from_shield_valid_address(self):
        """RED: Test extracting real email from valid shield address."""
        # Given a valid shield address
        shield_address = "yh.kim@cellophanemail.com"
        
        # When extracting the real email
        result = self.sender.extract_email_from_shield(shield_address)
        
        # Then it should return the configured username
        assert result == "goldenfermi@gmail.com"
    
    def test_extract_email_from_shield_invalid_domain(self):
        """RED: Test rejecting shield addresses from wrong domain."""
        # Given a shield address from wrong domain
        shield_address = "user@wrongdomain.com"
        
        # When extracting the real email
        result = self.sender.extract_email_from_shield(shield_address)
        
        # Then it should return None
        assert result is None
    
    def test_build_threading_headers_with_message_id(self):
        """RED: Test building threading headers with original message ID."""
        # Given an original email with message ID
        original_email = {
            'message_id': '<original123@sender.com>',
            'subject': 'Test Subject',
            'from': 'sender@example.com'
        }
        
        # When building threading headers
        headers = self.sender.build_threading_headers(original_email)
        
        # Then it should include In-Reply-To and References
        assert 'Message-ID' in headers
        assert headers['In-Reply-To'] == '<original123@sender.com>'
        assert headers['References'] == '<original123@sender.com>'
        assert '@cellophanemail.com>' in headers['Message-ID']
    
    def test_build_threading_headers_without_message_id(self):
        """RED: Test building threading headers without original message ID."""
        # Given an original email without message ID
        original_email = {
            'subject': 'Test Subject',
            'from': 'sender@example.com'
        }
        
        # When building threading headers
        headers = self.sender.build_threading_headers(original_email)
        
        # Then it should only include new Message-ID
        assert 'Message-ID' in headers
        assert 'In-Reply-To' not in headers
        assert 'References' not in headers
        assert '@cellophanemail.com>' in headers['Message-ID']
    
    def test_build_anti_spoofing_headers_without_thread_id(self):
        """RED: Test building anti-spoofing headers without thread ID."""
        # Given an original sender
        original_sender = "abusive@example.com"
        
        # When building anti-spoofing headers
        headers = self.sender.build_anti_spoofing_headers(original_sender)
        
        # Then it should use service domain and no Reply-To
        assert headers['From'] == 'CellophoneMail Shield <noreply@cellophanemail.com>'
        assert 'Reply-To' not in headers
    
    def test_build_anti_spoofing_headers_with_thread_id(self):
        """RED: Test building anti-spoofing headers with thread ID."""
        # Given an original sender and thread ID
        original_sender = "abusive@example.com"
        thread_id = "abc123"
        
        # When building anti-spoofing headers with thread ID
        headers = self.sender.build_anti_spoofing_headers(original_sender, thread_id)
        
        # Then it should include Reply-To with thread ID
        assert headers['From'] == 'CellophoneMail Shield <noreply@cellophanemail.com>'
        assert headers['Reply-To'] == 'thread-abc123@cellophanemail.com'
    
    def test_format_email_content_safe_classification(self):
        """RED: Test formatting safe email content."""
        # Given safe AI result and original email data
        ai_result = {'ai_classification': 'SAFE'}
        original_email_data = {
            'original_subject': 'Meeting tomorrow',
            'original_body': 'Hi, let\'s meet tomorrow at 2pm.',
            'original_sender': 'colleague@work.com'
        }
        
        # When formatting email content
        subject, content = self.sender.format_email_content(ai_result, original_email_data)
        
        # Then it should pass through content with footer
        assert subject == 'Meeting tomorrow'
        assert 'Hi, let\'s meet tomorrow at 2pm.' in content
        assert 'Protected by CellophoneMail Email Protection Service' in content
    
    def test_format_email_content_harmful_classification(self):
        """RED: Test formatting harmful email content."""
        # Given harmful AI result and original email data
        ai_result = {
            'ai_classification': 'HARMFUL',
            'horsemen_detected': ['criticism', 'contempt']
        }
        original_email_data = {
            'original_subject': 'You are terrible',
            'original_sender': 'abusive@example.com'
        }
        
        # When formatting email content
        subject, content = self.sender.format_email_content(ai_result, original_email_data)
        
        # Then it should format as filtered email
        assert subject == '[Filtered] You are terrible'
        assert '⚠️ Email filtered by CellophoneMail' in content
        assert 'Original sender: abusive@example.com' in content
        assert 'Detected: criticism, contempt' in content
        assert 'Classification: HARMFUL' in content
    
    def test_format_email_content_abusive_classification(self):
        """RED: Test formatting abusive email content."""
        # Given abusive AI result with no horsemen detected
        ai_result = {'ai_classification': 'ABUSIVE'}
        original_email_data = {
            'original_subject': 'Threatening message', 
            'original_sender': 'threat@example.com'
        }
        
        # When formatting email content
        subject, content = self.sender.format_email_content(ai_result, original_email_data)
        
        # Then it should format as filtered with default harmful content message
        assert subject == '[Filtered] Threatening message'
        assert 'Detected: harmful content' in content
        assert 'Classification: ABUSIVE' in content


class TestSendFilteredEmailIntegration:
    """Integration tests for send_filtered_email method that orchestrates all shared methods."""
    
    def setup_method(self):
        """Set up test fixtures with mock send_email method."""
        self.sent_messages = []  # Track sent messages
        
        class TestableEmailSender(BaseEmailSender):
            def __init__(self, service_domain, username, sent_messages_list):
                super().__init__(service_domain, username)
                self.sent_messages_list = sent_messages_list
            
            async def send_email(self, msg, recipient):
                """Mock implementation that captures sent messages."""
                self.sent_messages_list.append({
                    'msg': msg,
                    'recipient': recipient,
                    'subject': msg['Subject'],
                    'to': msg['To'],
                    'from': msg['From']
                })
                return "mock_send_result"
        
        self.sender = TestableEmailSender(
            service_domain='cellophanemail.com',
            username='goldenfermi@gmail.com',
            sent_messages_list=self.sent_messages
        )
    
    def test_send_filtered_email_safe_classification(self):
        """RED: Test complete flow for safe email."""
        # Given a safe AI result and original email data
        recipient_shield_address = "user@cellophanemail.com"
        ai_result = {'ai_classification': 'SAFE'}
        original_email_data = {
            'original_subject': 'Good news!',
            'original_body': 'Great job on the project!',
            'original_sender': 'boss@company.com',
            'message_id': '<abc123@company.com>'
        }
        
        # When sending filtered email (this is async)
        import asyncio
        result = asyncio.run(self.sender.send_filtered_email(
            recipient_shield_address, ai_result, original_email_data
        ))
        
        # Then it should send the email with correct formatting and headers
        assert len(self.sent_messages) == 1
        sent_msg = self.sent_messages[0]
        
        # Check recipient and subject
        assert sent_msg['to'] == 'goldenfermi@gmail.com'
        assert sent_msg['subject'] == 'Good news!'
        
        # Check that message has proper headers
        msg = sent_msg['msg']
        assert 'Message-ID' in msg
        assert 'In-Reply-To' in msg
        assert msg['In-Reply-To'] == '<abc123@company.com>'
        assert 'CellophoneMail Shield' in msg['From']
    
    def test_send_filtered_email_harmful_classification(self):
        """RED: Test complete flow for harmful email."""
        # Given a harmful AI result
        recipient_shield_address = "user@cellophanemail.com"
        ai_result = {
            'ai_classification': 'HARMFUL',
            'horsemen_detected': ['criticism', 'contempt']
        }
        original_email_data = {
            'original_subject': 'You are incompetent',
            'original_sender': 'toxic@example.com'
        }
        
        # When sending filtered email
        import asyncio
        result = asyncio.run(self.sender.send_filtered_email(
            recipient_shield_address, ai_result, original_email_data
        ))
        
        # Then it should send filtered email
        assert len(self.sent_messages) == 1
        sent_msg = self.sent_messages[0]
        
        assert sent_msg['subject'] == '[Filtered] You are incompetent'
        assert sent_msg['to'] == 'goldenfermi@gmail.com'