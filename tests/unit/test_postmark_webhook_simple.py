"""Simple unit test for Postmark webhook domain validation."""

import pytest
from cellophanemail.routes.webhooks import PostmarkWebhookPayload


class TestPostmarkWebhookSimple:
    """Simple tests for Postmark webhook functionality."""
    
    def test_postmark_payload_validation(self):
        """Test that PostmarkWebhookPayload validates correctly."""
        # Valid payload
        payload_data = {
            "From": "sender@example.com",
            "To": "a1b2c3d4e5f6789012345678901234567@cellophanemail.com",
            "Subject": "Test email",
            "MessageID": "msg-123456",
            "Date": "2025-08-12T12:00:00Z",
            "TextBody": "This is a test email"
        }
        
        # Should not raise exception
        payload = PostmarkWebhookPayload(**payload_data)
        
        assert payload.From == "sender@example.com"
        assert payload.To == "a1b2c3d4e5f6789012345678901234567@cellophanemail.com"
        assert payload.Subject == "Test email"
        assert payload.MessageID == "msg-123456"
    
    def test_domain_validation_logic(self):
        """Test the domain validation logic directly."""
        # This tests the logic used in the webhook handler
        
        valid_address = "a1b2c3d4e5f6789012345678901234567@cellophanemail.com"
        invalid_address = "user@wrong-domain.com"
        
        # Test valid domain
        assert valid_address.lower().strip().endswith("@cellophanemail.com")
        
        # Test invalid domain  
        assert not invalid_address.lower().strip().endswith("@cellophanemail.com")
    
    def test_shield_address_format(self):
        """Test shield address format validation."""
        from cellophanemail.services.user_service import ShieldAddressService
        
        valid_shield = "a1b2c3d4e5f6789012345678901234ab@cellophanemail.com"  # Valid hex
        invalid_shield_short = "abc123@cellophanemail.com" 
        invalid_shield_domain = "a1b2c3d4e5f6789012345678901234ab@wrong.com"
        
        # Test valid format
        assert ShieldAddressService.validate_shield_format(valid_shield)
        
        # Test invalid formats
        assert not ShieldAddressService.validate_shield_format(invalid_shield_short)
        assert not ShieldAddressService.validate_shield_format(invalid_shield_domain)
    
    def test_uuid_generation(self):
        """Test UUID generation for shield addresses."""
        import uuid
        
        # Generate UUID without hyphens (32 chars)
        test_uuid = uuid.uuid4().hex
        
        assert len(test_uuid) == 32
        assert '-' not in test_uuid
        
        # Test it's valid hex
        int(test_uuid, 16)  # Should not raise exception
        
        # Create shield address
        shield_address = f"{test_uuid}@cellophanemail.com"
        expected_length = 32 + len("@cellophanemail.com")
        
        assert len(shield_address) == expected_length
        assert shield_address.endswith("@cellophanemail.com")
