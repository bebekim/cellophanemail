#!/usr/bin/env python3
"""Test email sending with dry-run mode to avoid quota usage."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Force dry-run mode
os.environ['POSTMARK_DRY_RUN'] = 'true'
os.environ['CELLOPHANEMAIL_TEST_MODE'] = 'true'

from cellophanemail.providers.postmark.provider import PostmarkProvider
from cellophanemail.providers.contracts import EmailMessage, ProviderConfig


def test_dry_run():
    """Test Postmark provider in dry-run mode."""
    asyncio.run(_test_dry_run())

async def _test_dry_run():
    """Internal async test function."""
    
    print("=" * 60)
    print("Testing Postmark Provider in DRY-RUN Mode")
    print("=" * 60)
    print()
    
    # Initialize provider with dry-run
    provider = PostmarkProvider()
    config = ProviderConfig(
        enabled=True,
        config={
            "server_token": "test-token-dry-run",
            "from_address": "test@cellophanemail.com",
            "dry_run": True  # Explicit dry-run
        }
    )
    
    await provider.initialize(config)
    
    # Create test messages
    test_messages = [
        EmailMessage(
            message_id="test-001",
            from_address="sender@example.com",
            to_addresses=["user@example.com"],
            subject="Test Message 1 - Simple",
            text_body="This is a test message in dry-run mode.",
            html_body=None
        ),
        EmailMessage(
            message_id="test-002",
            from_address="sender@example.com",
            to_addresses=["user1@example.com", "user2@example.com"],
            subject="Test Message 2 - Multiple Recipients",
            text_body="Testing multiple recipients.",
            html_body="<p>Testing <b>multiple</b> recipients.</p>"
        ),
        EmailMessage(
            message_id="test-003",
            from_address="sender@example.com",
            to_addresses=["shield.abc123@cellophanemail.com"],
            subject="Test Message 3 - Shield Address",
            text_body="Testing shield address forwarding.",
            html_body=None,
            shield_address="shield.abc123@cellophanemail.com"
        )
    ]
    
    # Send test messages
    for msg in test_messages:
        print(f"\n📧 Sending message: {msg.subject}")
        success = await provider.send_message(msg)
        if success:
            print(f"✅ Message sent successfully (dry-run)")
        else:
            print(f"❌ Message failed")
    
    print(f"\n📊 Total messages sent (dry-run): {provider.sent_count}")
    print("\n✨ Test complete! No quota was used.")
    
    # Check if log file was created
    if os.getenv('POSTMARK_LOG_DRY_RUN'):
        from datetime import datetime
        log_file = f"postmark_dry_run_{datetime.now().strftime('%Y%m%d')}.jsonl"
        if os.path.exists(log_file):
            print(f"\n📁 Dry-run log saved to: {log_file}")
            with open(log_file, 'r') as f:
                lines = f.readlines()
                print(f"   Contains {len(lines)} entries")


def test_with_registry():
    """Test using the provider registry."""
    asyncio.run(_test_with_registry())

async def _test_with_registry():
    """Internal async test function."""
    from cellophanemail.providers.registry import get_provider_registry
    
    print("\n" + "=" * 60)
    print("Testing Provider Registry")
    print("=" * 60)
    print()
    
    # Get registry (no license key = open source mode)
    registry = get_provider_registry()
    
    # List available providers
    print("Available providers:")
    for provider_info in registry.get_available_providers():
        print(f"  - {provider_info['name']}: {provider_info['description']}")
        print(f"    Features: {', '.join(provider_info['features'])}")
    
    print("\nAll providers (with availability):")
    for provider_info in registry.list_all_providers():
        status = "✅" if provider_info['available'] else "🔒"
        print(f"  {status} {provider_info['name']} ({provider_info['license']})")


if __name__ == "__main__":
    print("\n🔧 Environment Configuration:")
    print(f"  POSTMARK_DRY_RUN: {os.getenv('POSTMARK_DRY_RUN', 'not set')}")
    print(f"  CELLOPHANEMAIL_TEST_MODE: {os.getenv('CELLOPHANEMAIL_TEST_MODE', 'not set')}")
    print(f"  POSTMARK_LOG_DRY_RUN: {os.getenv('POSTMARK_LOG_DRY_RUN', 'not set')}")
    print()
    
    asyncio.run(test_dry_run())
    asyncio.run(test_with_registry())