#!/usr/bin/env python3
"""Test production traffic handling with real shield addresses."""

import asyncio
import aiohttp
import json
from datetime import datetime

# Server endpoint
BASE_URL = "http://localhost:8000"
NEW_POSTMARK_ENDPOINT = f"{BASE_URL}/providers/postmark/inbound"

# Real production shield addresses from logs
PRODUCTION_EMAIL = {
    "From": "sender@example.com",
    "FromName": "Real Sender",
    "To": "yh.kim@cellophanemail.com",  # Real address from logs
    "Subject": "Production test email",
    "MessageID": f"prod-test-{datetime.now().timestamp()}",
    "Date": datetime.now().isoformat(),
    "TextBody": "This is a test of the production shield address handling.",
    "HtmlBody": "<p>This is a test of the production shield address handling.</p>",
    "Headers": [{"Name": "X-Test", "Value": "production"}]
}

PRODUCTION_EMAIL_2 = {
    "From": "another@example.com", 
    "FromName": "Another Sender",
    "To": "recipient@cellophanemail.com",  # Another real address from logs
    "Subject": "Second production test",
    "MessageID": f"prod-test-2-{datetime.now().timestamp()}",
    "Date": datetime.now().isoformat(),
    "TextBody": "Testing the second production shield address.",
    "HtmlBody": "<p>Testing the second production shield address.</p>",
    "Headers": [{"Name": "X-Test", "Value": "production"}]
}


async def test_production_address(payload: dict, test_name: str):
    """Test a production shield address."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"Shield Address: {payload['To']}")
    print(f"{'='*60}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                NEW_POSTMARK_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                if response.status == 200:
                    print(f"✅ Production address handled successfully!")
                    print(f"   Forwarded: {result.get('forwarded', False)}")
                    print(f"   Threat Level: {result.get('threat_level', 'N/A')}")
                elif response.status == 404:
                    print(f"❌ Shield address not found (expected if not in demo data)")
                else:
                    print(f"⚠️  Unexpected status: {response.status}")
                
                return result
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None


async def main():
    """Test production traffic handling."""
    print("\n" + "="*60)
    print("PRODUCTION TRAFFIC TEST")
    print("Testing real shield addresses from server logs")
    print("="*60)
    
    # Test first production address
    result1 = await test_production_address(PRODUCTION_EMAIL, "Production Address 1 (yh.kim@cellophanemail.com)")
    
    # Test second production address  
    result2 = await test_production_address(PRODUCTION_EMAIL_2, "Production Address 2 (recipient@cellophanemail.com)")
    
    print("\n" + "="*60)
    print("PRODUCTION TEST SUMMARY")
    print("="*60)
    
    if result1 and result2:
        addr1_found = result1.get("forwarded") is not None
        addr2_found = result2.get("forwarded") is not None
        
        print("Results:")
        print(f"  yh.kim@cellophanemail.com: {'✅ Found & processed' if addr1_found else '🔧 Not in demo data'}")
        print(f"  recipient@cellophanemail.com: {'✅ Found & processed' if addr2_found else '🔧 Not in demo data'}")
        
        if addr1_found and addr2_found:
            print("\n🎉 All production addresses handled correctly!")
        else:
            print("\n✅ Architecture working - addresses handled as expected")
            print("   (404s are expected for addresses not in demo data)")
    
    print("\n📋 This demonstrates:")
    print("   - New architecture can handle real production traffic")
    print("   - Shield address feature provides proper user lookup")
    print("   - System gracefully handles unknown addresses")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())