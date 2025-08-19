#!/usr/bin/env python3
"""Test script to verify legacy webhook fix."""

import json
import requests

# Postmark-style webhook data (similar to production)
test_payload = {
    "From": "test-sender@example.com",
    "FromName": "Test Sender", 
    "To": "yh.kim@cellophanemail.com",
    "ToFull": [{"Email": "yh.kim@cellophanemail.com", "Name": ""}],
    "Subject": "Legacy fix verification test",
    "MessageID": "legacy-fix-test-123456",
    "Date": "Mon, 15 Jan 2024 10:00:00 +0000",
    "TextBody": "This is a test to verify the legacy webhook endpoint works after adding shield_address to EmailMessage.",
    "HtmlBody": "<p>This is a test to verify the legacy webhook endpoint works after adding shield_address to EmailMessage.</p>",
    "Headers": [
        {"Name": "X-Test", "Value": "Legacy-Fix-Test"}
    ],
    "Attachments": []
}

def test_endpoint(url, name):
    """Test an endpoint with the payload."""
    print(f"\n🧪 Testing {name} endpoint: {url}")
    try:
        response = requests.post(url, json=test_payload, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)}")
        else:
            print(f"   Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    base_url = "http://localhost:8000"
    
    print("🔧 Testing Legacy Webhook Fix")
    print("=" * 40)
    
    # Test new provider endpoint
    new_endpoint_ok = test_endpoint(f"{base_url}/providers/postmark/inbound", "NEW Provider")
    
    # Test legacy webhook endpoint  
    legacy_endpoint_ok = test_endpoint(f"{base_url}/webhooks/postmark", "LEGACY Webhook")
    
    print("\n📊 Summary:")
    print(f"   NEW Provider Endpoint: {'✅ PASS' if new_endpoint_ok else '❌ FAIL'}")
    print(f"   LEGACY Webhook Endpoint: {'✅ PASS' if legacy_endpoint_ok else '❌ FAIL'}")
    
    if new_endpoint_ok and legacy_endpoint_ok:
        print("\n🎉 All endpoints working! Legacy fix successful.")
    else:
        print("\n⚠️  Some endpoints failed. Check server logs for details.")

if __name__ == "__main__":
    main()