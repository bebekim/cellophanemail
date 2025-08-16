#!/usr/bin/env python3
"""Test webhook with real user and shield address."""

import requests
import json

def test_safe_email():
    """Test with the real shield address we created."""
    payload = {
        "From": "friend@example.com",
        "To": "c5b8bec80d4046139e94176626b923d6@cellophanemail.com",
        "Subject": "Hello friend!",
        "MessageID": "test-safe-123",
        "Date": "2025-08-14T12:00:00Z",
        "TextBody": "Hi! How are you doing? Just wanted to check in.",
        "HtmlBody": "<p>Hi! How are you doing? Just wanted to check in.</p>",
        "Headers": [{"Name": "X-Test", "Value": "safe-email"}],
        "Attachments": []
    }
    
    print("🟢 Testing SAFE email with real user...")
    print(f"   To: {payload['To']}")
    
    response = requests.post("http://localhost:8000/webhooks/postmark", json=payload)
    
    print(f"✅ Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_toxic_email():
    """Test toxic email with real user (should be blocked)."""
    payload = {
        "From": "angry@example.com",
        "To": "c5b8bec80d4046139e94176626b923d6@cellophanemail.com",
        "Subject": "You're pathetic",
        "MessageID": "test-toxic-456", 
        "Date": "2025-08-14T12:00:00Z",
        "TextBody": "You always mess everything up. You're so stupid and worthless. I'm done talking to you.",
        "Headers": [{"Name": "X-Test", "Value": "toxic-email"}],
        "Attachments": []
    }
    
    print("\n🔴 Testing TOXIC email with real user...")
    print(f"   To: {payload['To']}")
    
    response = requests.post("http://localhost:8000/webhooks/postmark", json=payload)
    
    print(f"✅ Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Testing Postmark webhook with REAL user and shield address")
    print("=" * 60)
    
    try:
        test_safe_email()
        test_toxic_email()
        print("\n🎉 End-to-end webhook testing complete!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running! Start with: PYTHONPATH=src uv run uvicorn cellophanemail.app:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")