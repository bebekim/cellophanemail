#!/usr/bin/env python3
"""Manual test script for Postmark webhook endpoint."""

import requests
import json
import uuid
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhooks/postmark"  # Update with your URL

def run_safe_email_test():
    """Test with a safe, clean email."""
    shield_uuid = uuid.uuid4().hex  # Generate valid UUID without hyphens
    
    payload = {
        "From": "friend@example.com",
        "To": f"{shield_uuid}@cellophanemail.com",
        "Subject": "Hey, how are you?",
        "MessageID": f"msg-{uuid.uuid4()}",
        "Date": datetime.now().isoformat() + "Z",
        "TextBody": "Hi! Just wanted to check in and see how you're doing. Hope all is well!",
        "HtmlBody": "<p>Hi! Just wanted to check in and see how you're doing. Hope all is well!</p>",
        "Headers": [
            {"Name": "X-Mailer", "Value": "Gmail"},
            {"Name": "X-Priority", "Value": "3"}
        ],
        "Attachments": []
    }
    
    print(f"📧 Testing SAFE email to shield: {shield_uuid}@cellophanemail.com")
    print(f"   From: {payload['From']}")
    print(f"   Subject: {payload['Subject']}")
    
    response = requests.post(WEBHOOK_URL, json=payload)
    
    print(f"\n✅ Response Status: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    
    return response

def run_toxic_email_test():
    """Test with a toxic email containing Four Horsemen."""
    shield_uuid = uuid.uuid4().hex
    
    payload = {
        "From": "angry@example.com", 
        "To": f"{shield_uuid}@cellophanemail.com",
        "Subject": "You're pathetic",
        "MessageID": f"msg-{uuid.uuid4()}",
        "Date": datetime.now().isoformat() + "Z",
        "TextBody": """You always mess everything up. You're so stupid and worthless. 
        I'm done talking to you. You're pathetic and I'm better than you in every way.
        This is all your fault, not mine.""",
        "HtmlBody": "<p>You always mess everything up. You're so <b>stupid</b> and worthless.</p>",
        "Headers": [
            {"Name": "X-Mailer", "Value": "Angry Mail Client"}
        ],
        "Attachments": []
    }
    
    print(f"\n🔥 Testing TOXIC email to shield: {shield_uuid}@cellophanemail.com")
    print(f"   From: {payload['From']}")
    print(f"   Subject: {payload['Subject']}")
    
    response = requests.post(WEBHOOK_URL, json=payload)
    
    print(f"\n✅ Response Status: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    
    return response

def run_invalid_domain_test():
    """Test with invalid domain (should be rejected)."""
    
    payload = {
        "From": "test@example.com",
        "To": "user@wrongdomain.com",  # Wrong domain
        "Subject": "Test",
        "MessageID": f"msg-{uuid.uuid4()}",
        "Date": datetime.now().isoformat() + "Z",
        "TextBody": "This should be rejected"
    }
    
    print(f"\n❌ Testing INVALID domain: user@wrongdomain.com")
    
    response = requests.post(WEBHOOK_URL, json=payload)
    
    print(f"\n✅ Response Status: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    
    return response

def run_postmark_default_test():
    """Test using Postmark's default inbound address format."""
    
    # This simulates an email sent to Postmark's default address
    # Replace with your actual Postmark inbound address if you have it
    payload = {
        "From": "sender@example.com",
        "To": "e33bf218491800fd739e00a528ecb302@inbound.postmarkapp.com",
        "Subject": "Test via Postmark default",
        "MessageID": f"msg-{uuid.uuid4()}",
        "Date": datetime.now().isoformat() + "Z",
        "TextBody": "Testing with Postmark's default inbound address",
        "Headers": [],
        "Attachments": []
    }
    
    print(f"\n📮 Testing Postmark default address format")
    print(f"   To: {payload['To']}")
    
    response = requests.post(WEBHOOK_URL, json=payload)
    
    print(f"\n✅ Response Status: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    
    return response

def main():
    """Run all webhook tests."""
    print("=" * 60)
    print("POSTMARK WEBHOOK MANUAL TEST")
    print("=" * 60)
    print(f"Webhook URL: {WEBHOOK_URL}")
    print("\nMake sure your Litestar server is running!")
    print("Run: PYTHONPATH=src uv run uvicorn cellophanemail.app:app --reload")
    print("=" * 60)
    
    print("\nStarting tests...")
    
    # Run tests
    try:
        # Test 1: Invalid domain (should fail)
        run_invalid_domain_test()
        
        # Test 2: Safe email (should forward if user exists)
        run_safe_email_test()
        
        # Test 3: Toxic email (should block)
        run_toxic_email_test()
        
        # Test 4: Postmark default format
        run_postmark_default_test()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("\nNote: Shield addresses won't have users unless you create them first.")
        print("The webhook will return 404 for unknown shield addresses (expected).")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to webhook URL!")
        print(f"   Make sure your server is running at {WEBHOOK_URL}")
        print("   Run: PYTHONPATH=src uv run uvicorn cellophanemail.app:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    main()