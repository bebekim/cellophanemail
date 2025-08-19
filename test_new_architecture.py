#!/usr/bin/env python3
"""Test the new architecture with provider + feature separation."""

import asyncio
import aiohttp
import json
from datetime import datetime

# Server endpoint
BASE_URL = "http://localhost:8000"
NEW_POSTMARK_ENDPOINT = f"{BASE_URL}/providers/postmark/inbound"
OLD_POSTMARK_ENDPOINT = f"{BASE_URL}/webhooks/postmark"

# Test emails
SAFE_EMAIL = {
    "From": "friend@example.com",
    "FromName": "Good Friend",
    "To": "shield123@cellophanemail.com",
    "Subject": "Hey, how are you?",
    "MessageID": f"safe-{datetime.now().timestamp()}",
    "Date": datetime.now().isoformat(),
    "TextBody": "Just checking in! Hope you're having a great day.",
    "HtmlBody": "<p>Just checking in! Hope you're having a great day.</p>",
    "Headers": [{"Name": "X-Test", "Value": "new-architecture"}]
}

HARMFUL_EMAIL = {
    "From": "troll@badactor.com",
    "FromName": "Internet Troll",
    "To": "shield456@cellophanemail.com",
    "Subject": "You're worthless",
    "MessageID": f"harmful-{datetime.now().timestamp()}",
    "Date": datetime.now().isoformat(),
    "TextBody": "You're such an idiot and nobody likes you. Everyone hates you.",
    "HtmlBody": "<p>You're such an idiot and nobody likes you. Everyone hates you.</p>",
    "Headers": [{"Name": "X-Test", "Value": "new-architecture"}]
}

PHISHING_EMAIL = {
    "From": "scammer@phishing.net",
    "FromName": "Account Security",
    "To": "shield789@cellophanemail.com",
    "Subject": "Urgent: Verify your account",
    "MessageID": f"phishing-{datetime.now().timestamp()}",
    "Date": datetime.now().isoformat(),
    "TextBody": "Your account has been suspended! Click this link immediately to verify your account or lose access forever. Act now!",
    "HtmlBody": "<p>Your account has been suspended! Click this link immediately to verify your account or lose access forever. Act now!</p>",
    "Headers": [{"Name": "X-Test", "Value": "new-architecture"}]
}


async def test_endpoint(endpoint: str, payload: dict, test_name: str):
    """Test a specific endpoint with payload."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"Endpoint: {endpoint}")
    print(f"{'='*60}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                print(f"Status Code: {response.status}")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Analyze response
                if response.status == 200:
                    if "forwarded" in result:
                        if result["forwarded"]:
                            print(f"✅ Email FORWARDED")
                            print(f"   Threat Level: {result.get('threat_level', 'N/A')}")
                            print(f"   Toxicity: {result.get('toxicity_score', 0):.2f}")
                        else:
                            print(f"🛡️ Email BLOCKED")
                            print(f"   Reason: {result.get('block_reason', 'N/A')}")
                            print(f"   Threat Level: {result.get('threat_level', 'N/A')}")
                            print(f"   Toxicity: {result.get('toxicity_score', 0):.2f}")
                    else:
                        print("⚠️  Response format different than expected")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown')}")
                
                return result
                
        except aiohttp.ClientError as e:
            print(f"❌ Connection error: {e}")
            return None


async def main():
    """Run the new architecture test."""
    print("\n" + "="*60)
    print("NEW ARCHITECTURE TEST")
    print("Provider: Postmark")
    print("Feature: Email Protection (Four Horsemen)")
    print("="*60)
    
    # Check server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    print("✅ Server is running")
                else:
                    print("❌ Server health check failed")
                    return
    except:
        print("❌ Cannot connect to server at", BASE_URL)
        print("   Make sure ./bin/dev is running")
        return
    
    # Test new architecture endpoint
    print("\n" + "="*60)
    print("TESTING NEW ARCHITECTURE")
    print("="*60)
    
    # Test SAFE email
    result1 = await test_endpoint(NEW_POSTMARK_ENDPOINT, SAFE_EMAIL, "SAFE Email (New Architecture)")
    
    # Test HARMFUL email
    result2 = await test_endpoint(NEW_POSTMARK_ENDPOINT, HARMFUL_EMAIL, "HARMFUL Email (New Architecture)")
    
    # Test PHISHING email
    result3 = await test_endpoint(NEW_POSTMARK_ENDPOINT, PHISHING_EMAIL, "PHISHING Email (New Architecture)")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if result1 and result2 and result3:
        safe_forwarded = result1.get("forwarded", False)
        harmful_blocked = not result2.get("forwarded", True)
        phishing_blocked = not result3.get("forwarded", True)
        
        print("Results:")
        print(f"  Safe Email: {'✅ Forwarded' if safe_forwarded else '❌ Blocked (should forward)'}")
        print(f"  Harmful Email: {'✅ Blocked' if harmful_blocked else '❌ Forwarded (should block)'}")
        print(f"  Phishing Email: {'✅ Blocked' if phishing_blocked else '❌ Forwarded (should block)'}")
        
        if safe_forwarded and harmful_blocked and phishing_blocked:
            print("\n🎉 NEW ARCHITECTURE WORKING PERFECTLY!")
            print("   - Provider (Postmark) correctly parses webhooks")
            print("   - Feature (Email Protection) correctly analyzes content")
            print("   - Integration between provider and feature is seamless")
        else:
            print("\n⚠️  Some tests did not pass as expected")
    else:
        print("❌ Could not complete all tests")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())