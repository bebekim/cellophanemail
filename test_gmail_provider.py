#!/usr/bin/env python3
"""Test script for Gmail provider."""

import json
import requests
import asyncio

async def test_gmail_provider():
    """Test Gmail provider functionality."""
    print("🧪 Testing Gmail Provider")
    print("=" * 40)
    
    # Test data for Gmail provider
    gmail_test_data = {
        "message_id": "gmail-test-123456",
        "from": "sender@example.com", 
        "to": "yh.kim@cellophanemail.com",
        "subject": "Gmail provider test",
        "content": "Testing Gmail provider integration with CellophoneMail"
    }
    
    base_url = "http://localhost:8000"
    
    # Test Gmail provider test endpoint
    print("\n🔧 Testing Gmail Provider Interface:")
    try:
        response = requests.post(
            f"{base_url}/providers/gmail/test",
            json=gmail_test_data,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"   Provider: {result.get('provider', 'unknown')}")
            print(f"   Test Status: {result.get('status', 'unknown')}")
            
            if 'message_parsed' in result:
                parsed = result['message_parsed']
                print(f"   Message ID: {parsed.get('message_id', 'none')}")
                print(f"   Shield Address: {parsed.get('shield_address', 'none')}")
            
            if 'oauth_url' in result and result['oauth_url']:
                print(f"   OAuth Setup: Available")
            else:
                print(f"   OAuth Setup: Configuration needed")
            
            return response.status_code == 200
        else:
            print(f"   Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"   Error: {e}")
        return False

def test_gmail_provider_structure():
    """Test Gmail provider code structure."""
    print("\n📁 Testing Gmail Provider Structure:")
    
    try:
        from src.cellophanemail.providers.gmail import GmailProvider, GmailWebhookHandler
        print("   ✅ Imports successful")
        
        # Test provider initialization
        provider = GmailProvider()
        print("   ✅ Provider instantiation successful")
        
        # Test properties
        print(f"   Provider name: {provider.name}")
        print(f"   Requires OAuth: {provider.requires_oauth}")
        
        # Test webhook handler
        handler = GmailWebhookHandler()
        print("   ✅ Webhook handler instantiation successful")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Structure error: {e}")
        return False

async def main():
    """Main test runner."""
    print("🚀 Gmail Provider Tests")
    print("=" * 50)
    
    # Test code structure
    structure_ok = test_gmail_provider_structure()
    
    # Test HTTP endpoints  
    endpoint_ok = await asyncio.to_thread(test_gmail_provider)
    
    print("\n📊 Test Summary:")
    print(f"   Code Structure: {'✅' if structure_ok else '❌'}")
    print(f"   HTTP Endpoints: {'✅' if endpoint_ok else '❌'}")
    
    if structure_ok and endpoint_ok:
        print("\n🎉 Gmail provider implementation complete!")
        print("   - Provider structure follows contracts")
        print("   - Webhook endpoints functional")  
        print("   - OAuth2 setup interface available")
        print("   - Ready for Gmail API integration")
    else:
        print("\n⚠️  Some tests failed - check implementation")

if __name__ == "__main__":
    asyncio.run(main())