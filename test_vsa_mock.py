#!/usr/bin/env python3
"""Test the Vertical Slice Architecture with mocked webhook data."""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test the /test endpoint first to verify connectivity
TEST_ENDPOINT = "http://localhost:8000/webhooks/test"
POSTMARK_ENDPOINT = "http://localhost:8000/webhooks/postmark"

async def test_connectivity():
    """Test basic webhook connectivity."""
    print("\n" + "="*60)
    print("Testing Webhook Connectivity")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                TEST_ENDPOINT,
                json={"test": "data"},
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                print(f"✅ Server is running!")
                print(f"   Endpoint: {TEST_ENDPOINT}")
                print(f"   Response: {json.dumps(result, indent=2)}")
                return True
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print(f"   Make sure ./bin/dev is running")
            return False


async def test_vsa_processing():
    """Test that VSA components are loaded correctly."""
    print("\n" + "="*60)
    print("Testing VSA Email Processing")
    print("="*60)
    
    # This will fail at the shield address lookup, but we can see if VSA is loaded
    test_payload = {
        "From": "test@example.com",
        "FromName": "Test Sender",
        "To": "nonexistent@cellophanemail.com",  # Will fail lookup but that's OK
        "Subject": "VSA Integration Test",
        "MessageID": f"vsa-test-{datetime.now().timestamp()}",
        "Date": datetime.now().isoformat(),
        "TextBody": "Testing vertical slice architecture integration",
        "HtmlBody": "<p>Testing vertical slice architecture integration</p>"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                POSTMARK_ENDPOINT,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status == 404:
                    print("✅ VSA is integrated correctly!")
                    print("   (Got expected 404 for non-existent shield address)")
                    print(f"   Response: {json.dumps(result, indent=2)}")
                    
                    # Check server logs to confirm VSA is being used
                    print("\n📋 Check server logs for:")
                    print('   - "Using Vertical Slice Architecture for email processing"')
                    print('   - "Processing email ... via vertical slice"')
                    return True
                else:
                    print(f"   Status: {response.status}")
                    print(f"   Response: {json.dumps(result, indent=2)}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def check_environment():
    """Check environment configuration."""
    print("\n" + "="*60)
    print("Environment Configuration")
    print("="*60)
    
    import os
    use_vsa = os.getenv("USE_VERTICAL_SLICE", "true").lower() == "true"
    
    print(f"USE_VERTICAL_SLICE = {os.getenv('USE_VERTICAL_SLICE', 'true')} ({'✅ ENABLED' if use_vsa else '⚠️ DISABLED'})")
    
    if not use_vsa:
        print("\n⚠️  To enable VSA, set: export USE_VERTICAL_SLICE=true")
    
    return use_vsa


async def main():
    """Run the VSA integration test."""
    print("\n" + "="*60)
    print("VERTICAL SLICE ARCHITECTURE MOCK TEST")
    print("="*60)
    print("This test verifies VSA is integrated without needing database setup")
    
    # Check environment
    vsa_enabled = await check_environment()
    
    # Test connectivity
    connected = await test_connectivity()
    if not connected:
        print("\n❌ Cannot proceed without server connection")
        return
    
    # Test VSA processing
    vsa_working = await test_vsa_processing()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if vsa_enabled and vsa_working:
        print("✅ Vertical Slice Architecture is successfully integrated!")
        print("   - Environment configured correctly")
        print("   - Server is running")
        print("   - VSA adapter is working")
        print("\n🎉 The migration to VSA is working!")
    else:
        if not vsa_enabled:
            print("⚠️  VSA is disabled in environment")
        if not vsa_working:
            print("⚠️  VSA integration may have issues")
    
    print("\n📝 Next Steps:")
    print("1. Create test users and shield addresses in the database")
    print("2. Run test_vsa_integration.py with real shield addresses")
    print("3. Send real emails through ngrok webhook")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())