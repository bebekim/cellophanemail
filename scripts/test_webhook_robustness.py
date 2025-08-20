#!/usr/bin/env python3
"""Test webhook endpoints with various invalid payloads to ensure robustness."""

import asyncio
import aiohttp
import json
import sys

async def webhook_robustness_test(base_url: str = "http://localhost:8000"):
    """Test webhook endpoints with various payloads."""
    
    test_cases = [
        {
            "name": "Empty payload",
            "payload": {},
            "expected_status": 400,
            "description": "Should handle empty requests gracefully"
        },
        {
            "name": "Null payload", 
            "payload": None,
            "expected_status": 400,
            "description": "Should handle null payloads"
        },
        {
            "name": "Missing required fields",
            "payload": {"From": "test@example.com"},
            "expected_status": 400,
            "description": "Should report missing required fields"
        },
        {
            "name": "Valid Postmark payload",
            "payload": {
                "From": "sender@example.com",
                "To": "shield.test123@cellophanemail.com", 
                "Subject": "Test Email",
                "MessageID": "test-12345",
                "Date": "2024-01-20T10:00:00Z",
                "TextBody": "This is a test email"
            },
            "expected_status": [200, 404],  # 404 is ok if shield address not found
            "description": "Should process valid payloads"
        }
    ]
    
    endpoint = f"{base_url}/providers/postmark/inbound"
    health_endpoint = f"{base_url}/providers/postmark/health"
    
    print(f"Testing webhook robustness at {endpoint}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test health check first
        try:
            async with session.post(health_endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data['status']}")
                else:
                    print(f"⚠️ Health check returned {response.status}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        print()
        
        # Test each case
        for test_case in test_cases:
            print(f"Testing: {test_case['name']}")
            print(f"Description: {test_case['description']}")
            
            try:
                headers = {'Content-Type': 'application/json'}
                data = json.dumps(test_case['payload']) if test_case['payload'] is not None else None
                
                async with session.post(endpoint, data=data, headers=headers) as response:
                    response_text = await response.text()
                    
                    expected_statuses = test_case['expected_status']
                    if not isinstance(expected_statuses, list):
                        expected_statuses = [expected_statuses]
                    
                    if response.status in expected_statuses:
                        print(f"✅ Status {response.status} (expected)")
                        
                        # Try to parse as JSON for better output
                        try:
                            response_json = json.loads(response_text)
                            if 'error' in response_json:
                                print(f"   Error message: {response_json['error']}")
                            elif 'status' in response_json:
                                print(f"   Status: {response_json['status']}")
                        except json.JSONDecodeError:
                            print(f"   Response: {response_text[:100]}")
                    else:
                        print(f"❌ Status {response.status} (expected {expected_statuses})")
                        print(f"   Response: {response_text[:200]}")
                        
            except Exception as e:
                print(f"❌ Request failed: {e}")
            
            print()
    
    print("Test complete!")
    print("\nIf you see ✅ for all tests, your webhook is robust to invalid requests.")

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    asyncio.run(webhook_robustness_test(base_url))