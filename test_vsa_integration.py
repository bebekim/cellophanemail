#!/usr/bin/env python3
"""Test the Vertical Slice Architecture integration with a real email."""

import asyncio
import aiohttp
import json
from datetime import datetime
import sys

# Test configuration
WEBHOOK_URL = "http://localhost:8000/webhooks/postmark"  # Local Litestar server
TEST_SHIELD_ADDRESS = "test@cellophanemail.com"  # You'll need to update this with a real shield address

# Test email payloads
SAFE_EMAIL = {
    "From": "friend@example.com",
    "FromName": "Friendly Sender",
    "To": TEST_SHIELD_ADDRESS,
    "Subject": "Hello! Just checking in",
    "MessageID": f"test-safe-{datetime.now().timestamp()}",
    "Date": datetime.now().isoformat(),
    "TextBody": "Hey there! Just wanted to see how you're doing. Hope all is well!",
    "HtmlBody": "<p>Hey there! Just wanted to see how you're doing. Hope all is well!</p>",
    "Headers": [
        {"Name": "X-Test", "Value": "VSA-Integration"}
    ]
}

HARMFUL_EMAIL = {
    "From": "troll@example.com", 
    "FromName": "Internet Troll",
    "To": TEST_SHIELD_ADDRESS,
    "Subject": "You're terrible",
    "MessageID": f"test-harmful-{datetime.now().timestamp()}",
    "Date": datetime.now().isoformat(),
    "TextBody": "You're an idiot and everyone hates you. You should just give up.",
    "HtmlBody": "<p>You're an idiot and everyone hates you. You should just give up.</p>",
    "Headers": [
        {"Name": "X-Test", "Value": "VSA-Integration"}
    ]
}


async def send_test_email(payload: dict, email_type: str):
    """Send a test email to the webhook endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing {email_type} email")
    print(f"{'='*60}")
    print(f"To: {payload['To']}")
    print(f"Subject: {payload['Subject']}")
    print(f"Message ID: {payload['MessageID']}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                print(f"\nResponse Status: {response.status}")
                print(f"Response Body: {json.dumps(result, indent=2)}")
                
                if response.status == 200:
                    if result.get("processing") == "forwarded":
                        print(f"✅ Email FORWARDED - Toxicity: {result.get('toxicity_score', 0):.2f}")
                    elif result.get("processing") == "blocked":
                        print(f"🛡️ Email BLOCKED - Reason: {result.get('block_reason')}")
                        if result.get("horsemen_detected"):
                            print(f"   Horsemen Detected: {', '.join(result['horsemen_detected'])}")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    
                return result
                
        except aiohttp.ClientError as e:
            print(f"❌ Connection error: {e}")
            print("\nMake sure the Flask server is running (./bin/dev)")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None


async def check_slice_usage():
    """Check if vertical slice architecture is being used."""
    print("\n" + "="*60)
    print("Checking Architecture Mode")
    print("="*60)
    
    # Check environment variable
    import os
    use_vsa = os.getenv("USE_VERTICAL_SLICE", "true").lower() == "true"
    
    if use_vsa:
        print("✅ Vertical Slice Architecture is ENABLED")
        print("   Emails will be processed through the new slice")
    else:
        print("⚠️  Traditional layered architecture is being used")
        print("   Set USE_VERTICAL_SLICE=true to use the new architecture")
    
    return use_vsa


async def main():
    """Run the integration test."""
    print("\n" + "="*60)
    print("VERTICAL SLICE ARCHITECTURE INTEGRATION TEST")
    print("="*60)
    
    # Check which architecture is being used
    using_vsa = await check_slice_usage()
    
    print(f"\n⚠️  IMPORTANT: Update TEST_SHIELD_ADDRESS in this script")
    print(f"   Current address: {TEST_SHIELD_ADDRESS}")
    print(f"   You need a valid shield address from your database")
    
    input("\nPress Enter to continue with testing...")
    
    # Test safe email
    safe_result = await send_test_email(SAFE_EMAIL, "SAFE")
    
    # Wait a bit between tests
    await asyncio.sleep(1)
    
    # Test harmful email
    harmful_result = await send_test_email(HARMFUL_EMAIL, "HARMFUL")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if using_vsa:
        print("Architecture: Vertical Slice (NEW)")
    else:
        print("Architecture: Traditional Layered")
    
    if safe_result and harmful_result:
        safe_forwarded = safe_result.get("processing") == "forwarded"
        harmful_blocked = harmful_result.get("processing") == "blocked"
        
        if safe_forwarded and harmful_blocked:
            print("✅ ALL TESTS PASSED!")
            print("   - Safe email was forwarded")
            print("   - Harmful email was blocked")
            if using_vsa:
                print("   - Vertical Slice Architecture is working correctly!")
        else:
            print("⚠️  UNEXPECTED RESULTS:")
            if not safe_forwarded:
                print("   - Safe email was NOT forwarded (expected: forwarded)")
            if not harmful_blocked:
                print("   - Harmful email was NOT blocked (expected: blocked)")
    else:
        print("❌ TESTS FAILED - Could not connect to server")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())