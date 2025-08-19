#!/usr/bin/env python3
"""Test the Postmark provider in isolation."""

import asyncio
from datetime import datetime
from src.cellophanemail.providers.postmark.provider import PostmarkProvider
from src.cellophanemail.providers.contracts import ProviderConfig

# Test webhook data (same format Postmark sends)
SAMPLE_POSTMARK_WEBHOOK = {
    "From": "sender@example.com",
    "FromName": "Test Sender",
    "To": "shield123@cellophanemail.com",
    "ToFull": [{"Email": "shield123@cellophanemail.com", "Name": ""}],
    "Subject": "Test Email via Postmark",
    "MessageID": f"test-{datetime.now().timestamp()}",
    "Date": datetime.now().isoformat(),
    "TextBody": "This is a test email body.",
    "HtmlBody": "<p>This is a test email body.</p>",
    "Headers": [
        {"Name": "X-Test", "Value": "true"},
        {"Name": "X-Provider", "Value": "postmark"}
    ],
    "Attachments": []
}


async def test_postmark_provider():
    """Test Postmark provider functionality."""
    print("\n" + "="*60)
    print("TESTING POSTMARK PROVIDER")
    print("="*60)
    
    # Create provider instance
    provider = PostmarkProvider()
    print(f"✅ Provider created: {provider.name}")
    print(f"   Requires OAuth: {provider.requires_oauth}")
    
    # Test parsing webhook data
    print("\n" + "-"*40)
    print("Testing webhook parsing...")
    
    try:
        email_message = await provider.receive_message(SAMPLE_POSTMARK_WEBHOOK)
        
        print("✅ Successfully parsed webhook data:")
        print(f"   Message ID: {email_message.message_id}")
        print(f"   From: {email_message.from_address}")
        print(f"   To: {email_message.to_addresses}")
        print(f"   Subject: {email_message.subject}")
        print(f"   Shield Address: {email_message.shield_address}")
        print(f"   Has Text Body: {email_message.text_body is not None}")
        print(f"   Has HTML Body: {email_message.html_body is not None}")
        print(f"   Headers Count: {len(email_message.headers or {})}")
        
        # Verify shield address detection
        if email_message.shield_address:
            print(f"✅ Shield address correctly identified: {email_message.shield_address}")
        else:
            print("❌ Failed to identify shield address")
            
    except Exception as e:
        print(f"❌ Failed to parse webhook: {e}")
        return False
    
    # Test with non-cellophanemail address
    print("\n" + "-"*40)
    print("Testing with non-cellophanemail address...")
    
    non_shield_data = SAMPLE_POSTMARK_WEBHOOK.copy()
    non_shield_data["To"] = "user@example.com"
    non_shield_data["ToFull"] = [{"Email": "user@example.com", "Name": ""}]
    
    try:
        email_message = await provider.receive_message(non_shield_data)
        if email_message.shield_address is None:
            print("✅ Correctly identified non-shield address")
        else:
            print("❌ Incorrectly identified as shield address")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test initialization (without actual API key)
    print("\n" + "-"*40)
    print("Testing provider initialization...")
    
    try:
        config = ProviderConfig(
            enabled=True,
            config={"server_token": "test-token", "from_address": "test@cellophanemail.com"}
        )
        await provider.initialize(config)
        print("✅ Provider initialized successfully")
        print(f"   From address: {provider.from_address}")
    except Exception as e:
        print(f"⚠️  Initialization test: {e}")
    
    print("\n" + "="*60)
    print("POSTMARK PROVIDER TEST COMPLETE")
    print("="*60)
    
    return True


if __name__ == "__main__":
    asyncio.run(test_postmark_provider())