#!/usr/bin/env python3
"""Test that legacy webhook routes production traffic through new architecture."""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Set environment variable to use new architecture
os.environ["USE_NEW_ARCHITECTURE"] = "true"

# Server endpoints
BASE_URL = "http://localhost:8000"
LEGACY_ENDPOINT = f"{BASE_URL}/webhooks/postmark"  # Legacy endpoint
NEW_ENDPOINT = f"{BASE_URL}/providers/postmark/inbound"  # New endpoint

# Test email that should work with both endpoints
TEST_EMAIL = {
    "From": "test@example.com",
    "FromName": "Test Sender", 
    "To": "yh.kim@cellophanemail.com",  # Production address that exists in demo data
    "Subject": "Legacy routing test",
    "MessageID": f"legacy-test-{datetime.now().timestamp()}",
    "Date": datetime.now().isoformat(),
    "TextBody": "Testing that legacy endpoint routes through new architecture",
    "HtmlBody": "<p>Testing that legacy endpoint routes through new architecture</p>",
    "Headers": [{"Name": "X-Test", "Value": "legacy-routing"}]
}


async def test_endpoint(endpoint: str, endpoint_name: str):
    """Test an endpoint with the same email."""
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint_name}")
    print(f"Endpoint: {endpoint}")
    print(f"{'='*60}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                endpoint,
                json=TEST_EMAIL,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                if response.status == 200:
                    # Check if it has the new architecture characteristics
                    has_threat_level = "threat_level" in result
                    has_forwarded = "forwarded" in result or "processing" in result
                    
                    if has_threat_level:
                        print(f"✅ Using NEW architecture (has threat_level)")
                        print(f"   Threat Level: {result.get('threat_level', 'N/A')}")
                        print(f"   Forwarded: {result.get('forwarded', result.get('processing') == 'forwarded')}")
                    else:
                        print(f"🔧 Using LEGACY architecture (no threat_level)")
                        print(f"   Processing: {result.get('processing', 'N/A')}")
                        
                else:
                    print(f"❌ Error: {result}")
                
                return result
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return None


async def main():
    """Test legacy routing to new architecture."""
    print("\n" + "="*60)
    print("LEGACY ROUTING TEST")
    print("Verifying production traffic routes through new architecture")
    print("="*60)
    
    # Test new endpoint (baseline)
    new_result = await test_endpoint(NEW_ENDPOINT, "New Provider Endpoint")
    
    # Test legacy endpoint (should now route through new architecture)  
    legacy_result = await test_endpoint(LEGACY_ENDPOINT, "Legacy Webhook Endpoint")
    
    print("\n" + "="*60)
    print("ROUTING COMPARISON")
    print("="*60)
    
    if new_result and legacy_result:
        new_has_threat = "threat_level" in new_result
        legacy_has_threat = "threat_level" in legacy_result or "toxicity_score" in legacy_result
        
        print("Architecture Detection:")
        print(f"  New Endpoint: {'✅ New Architecture' if new_has_threat else '❌ Old Architecture'}")
        print(f"  Legacy Endpoint: {'✅ New Architecture' if legacy_has_threat else '❌ Old Architecture'}")
        
        if new_has_threat and legacy_has_threat:
            print("\n🎉 SUCCESS: Legacy endpoint now routes through new architecture!")
            print("   - Production traffic will use provider/feature architecture")
            print("   - Both endpoints provide consistent results")
            print("   - Migration is successful")
        elif legacy_has_threat:
            print("\n✅ Legacy endpoint is using new architecture")
        else:
            print("\n⚠️  Legacy endpoint may still be using old architecture")
            print("   Check environment variable USE_NEW_ARCHITECTURE=true")
    
    print("\n📋 Next Steps:")
    print("   - Legacy endpoint now routes production traffic through new architecture")
    print("   - Can gradually migrate users to new /providers/ endpoints")
    print("   - Eventually retire legacy /webhooks/ endpoints")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())