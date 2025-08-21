#!/usr/bin/env python3
"""
Minimal integration test for code functionality.
Tests that the email pipeline works with just 1-2 emails.
No need to test all samples - if one works, the code works.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Force dry-run mode for tests
os.environ['POSTMARK_DRY_RUN'] = 'true'
os.environ['CELLOPHANEMAIL_TEST_MODE'] = 'true'

from cellophanemail.providers.contracts import EmailMessage, ProviderConfig
from cellophanemail.providers.postmark.provider import PostmarkProvider
from cellophanemail.providers.smtp.provider import SMTPProvider
from cellophanemail.providers.gmail.provider import GmailProvider
from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.providers.registry import get_provider_registry


class TestCodeFunctionality:
    """Test that the code works - not the analysis quality."""
    
    @pytest.fixture
    def sample_email(self):
        """Single test email for functionality testing."""
        return EmailMessage(
            message_id="test-func-001",
            from_address="sender@example.com",
            to_addresses=["shield.test123@cellophanemail.com"],
            subject="Functionality Test Email",
            text_body="This is a simple test to verify the pipeline works.",
            html_body=None,
            shield_address="shield.test123@cellophanemail.com"
        )
    
    @pytest.mark.asyncio
    async def test_postmark_provider_pipeline(self, sample_email):
        """Test Postmark provider can receive and send (dry-run)."""
        provider = PostmarkProvider()
        config = ProviderConfig(
            enabled=True,
            config={"dry_run": True, "server_token": "test", "from_address": "test@example.com"}
        )
        await provider.initialize(config)
        
        # Test receiving webhook data
        webhook_data = {
            "MessageID": "test-001",
            "From": "sender@example.com",
            "To": "shield.test123@cellophanemail.com",
            "Subject": "Test",
            "TextBody": "Test message"
        }
        
        received = await provider.receive_message(webhook_data)
        assert received.message_id == "test-001"
        assert received.shield_address == "shield.test123@cellophanemail.com"
        
        # Test sending (dry-run)
        sent = await provider.send_message(sample_email)
        assert sent == True
        assert provider.sent_count == 1  # Verify dry-run counter
        
        print("✅ Postmark pipeline works")
    
    @pytest.mark.asyncio
    async def test_smtp_provider_pipeline(self, sample_email):
        """Test SMTP provider basic functionality."""
        provider = SMTPProvider()
        config = ProviderConfig(
            enabled=True,
            config={"smtp_host": None}  # No host = no actual sending
        )
        await provider.initialize(config)
        
        # Test receiving
        smtp_data = {
            "from_address": "sender@example.com",
            "to_addresses": ["shield.test123@cellophanemail.com"],
            "subject": "Test",
            "text_body": "Test message"
        }
        
        received = await provider.receive_message(smtp_data)
        assert received.shield_address == "shield.test123@cellophanemail.com"
        
        print("✅ SMTP pipeline works")
    
    @pytest.mark.asyncio
    async def test_protection_processor(self, sample_email):
        """Test email protection processor with one email."""
        processor = EmailProtectionProcessor()
        
        # Process one email through protection
        result = await processor.process_email(
            sample_email,
            user_email="user@example.com"
        )
        
        assert result is not None
        assert hasattr(result, 'should_forward')
        assert hasattr(result, 'analysis')
        
        print(f"✅ Protection processor works - Decision: forward={result.should_forward}")
    
    @pytest.mark.asyncio
    async def test_provider_registry(self):
        """Test provider registry loads providers correctly."""
        registry = get_provider_registry()
        
        # Test available providers (no license = open source only)
        available = registry.get_available_providers()
        provider_names = [p['name'] for p in available]
        
        assert 'gmail' in provider_names
        assert 'smtp' in provider_names
        # Postmark should not be available without license
        
        # Test loading a provider
        smtp_provider = registry.get_provider('smtp')
        assert smtp_provider is not None
        assert smtp_provider.name == 'smtp'
        
        print(f"✅ Registry works - {len(available)} providers available")
    
    @pytest.mark.asyncio
    async def test_webhook_to_forward_flow(self):
        """Test complete flow: webhook → analysis → forward (dry-run)."""
        # This is the critical path that needs to work
        
        # 1. Receive webhook
        provider = PostmarkProvider()
        config = ProviderConfig(
            enabled=True,
            config={"dry_run": True, "server_token": "test", "from_address": "test@example.com"}
        )
        await provider.initialize(config)
        
        webhook_data = {
            "MessageID": "flow-test-001",
            "From": "friend@example.com",
            "To": "shield.abc123@cellophanemail.com",
            "Subject": "Hello!",
            "TextBody": "Hope you're doing well!"
        }
        
        email = await provider.receive_message(webhook_data)
        
        # 2. Process through protection
        processor = EmailProtectionProcessor()
        result = await processor.process_email(email, "realuser@example.com")
        
        # 3. Forward if safe (dry-run)
        if result.should_forward:
            sent = await provider.send_message(email)
            assert sent == True
        
        print(f"✅ Complete flow works - Email {'forwarded' if result.should_forward else 'blocked'}")


def run_minimal_tests():
    """Run minimal integration tests."""
    print("\n" + "="*60)
    print("MINIMAL INTEGRATION TESTS - Code Functionality")
    print("="*60)
    print("\nTesting with 1 email to verify pipeline works...")
    print("(Not testing analysis quality - just that code executes)\n")
    
    # Run the tests
    import subprocess
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\n✅ All code functionality tests passed!")
        print("The pipeline works correctly.")
    else:
        print("\n❌ Some tests failed - check the code")
    
    return result.returncode


if __name__ == "__main__":
    exit(run_minimal_tests())
