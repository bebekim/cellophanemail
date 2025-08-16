#!/usr/bin/env python3
"""Test webhook with just safe email to verify delivery attempt."""

import requests
import json

def test_safe_email_delivery():
    """Test webhook with safe email to see delivery attempt."""
    payload = {
        "From": "friend@example.com",
        "To": "c5b8bec80d4046139e94176626b923d6@cellophanemail.com", 
        "Subject": "Hello friend!",
        "MessageID": "test-delivery-123",
        "Date": "2025-08-14T12:00:00Z",
        "TextBody": "Hi! How are you doing? Just wanted to check in and see how things are going.",
        "HtmlBody": "<p>Hi! How are you doing? Just wanted to check in and see how things are going.</p>",
        "Headers": [{"Name": "X-Test", "Value": "delivery-test"}],
        "Attachments": []
    }
    
    print("🚀 Testing email delivery integration...")
    print(f"   To: {payload['To']}")
    
    response = requests.post("http://localhost:8000/webhooks/postmark", json=payload)
    
    print(f"✅ Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    try:
        test_safe_email_delivery()
    except requests.exceptions.ConnectionError:
        print("❌ Server not running! Start server first")
    except Exception as e:
        print(f"❌ Error: {e}")