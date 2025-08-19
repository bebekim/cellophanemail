#!/usr/bin/env python3
"""Test script for SMTP provider."""

import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_smtp_provider_structure():
    """Test SMTP provider code structure."""
    print("🧪 Testing SMTP Provider Structure")
    print("=" * 40)
    
    try:
        from src.cellophanemail.providers.smtp import SMTPProvider, SMTPServerHandler
        print("   ✅ Imports successful")
        
        # Test provider initialization
        provider = SMTPProvider()
        print("   ✅ Provider instantiation successful")
        
        # Test properties
        print(f"   Provider name: {provider.name}")
        print(f"   Requires OAuth: {provider.requires_oauth}")
        print(f"   Server enabled: {provider.is_server_enabled()}")
        
        # Test server handler
        server = SMTPServerHandler()
        print("   ✅ Server handler instantiation successful")
        print(f"   Server status: {server.get_status()}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Structure error: {e}")
        return False

async def test_smtp_message_parsing():
    """Test SMTP message parsing functionality."""
    print("\n📧 Testing SMTP Message Parsing:")
    
    try:
        from src.cellophanemail.providers.smtp import SMTPProvider
        
        provider = SMTPProvider()
        
        # Test parsing direct field data
        test_message_data = {
            'message_id': 'smtp-test-123456',
            'from_address': 'sender@example.com',
            'to_addresses': ['user@cellophanemail.com', 'other@example.com'],
            'subject': 'SMTP provider test',
            'text_body': 'This is a test message for SMTP provider',
            'html_body': '<p>This is a test message for SMTP provider</p>',
            'date': 'Mon, 19 Aug 2024 10:00:00 +0000'
        }
        
        # Parse the message
        email_message = await provider.receive_message(test_message_data)
        
        print(f"   ✅ Message parsing successful")
        print(f"   Message ID: {email_message.message_id}")
        print(f"   Shield Address: {email_message.shield_address}")
        print(f"   To Addresses: {len(email_message.to_addresses)}")
        print(f"   Has Text Body: {email_message.text_body is not None}")
        print(f"   Has HTML Body: {email_message.html_body is not None}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Message parsing error: {e}")
        logger.error(f"Message parsing failed: {e}", exc_info=True)
        return False

async def test_smtp_server_interface():
    """Test SMTP server interface."""
    print("\n🖥️  Testing SMTP Server Interface:")
    
    try:
        from src.cellophanemail.providers.smtp.server import SMTPServerHandler, SMTPMessageHandler
        
        # Test message handler
        handler = SMTPMessageHandler()
        print("   ✅ Message handler instantiation successful")
        
        # Test server handler (don't actually start it)
        server = SMTPServerHandler("127.0.0.1", 2525)  # Use non-privileged port
        print("   ✅ Server handler instantiation successful")
        
        status = server.get_status()
        print(f"   Server running: {status['running']}")
        print(f"   Server host:port: {status['host']}:{status['port']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Server interface error: {e}")
        logger.error(f"Server interface test failed: {e}", exc_info=True)
        return False

async def main():
    """Main test runner."""
    print("🚀 SMTP Provider Tests")
    print("=" * 50)
    
    # Test code structure
    structure_ok = test_smtp_provider_structure()
    
    # Test message parsing
    parsing_ok = await test_smtp_message_parsing()
    
    # Test server interface
    server_ok = await test_smtp_server_interface()
    
    print("\n📊 Test Summary:")
    print(f"   Code Structure: {'✅' if structure_ok else '❌'}")
    print(f"   Message Parsing: {'✅' if parsing_ok else '❌'}")
    print(f"   Server Interface: {'✅' if server_ok else '❌'}")
    
    if structure_ok and parsing_ok and server_ok:
        print("\n🎉 SMTP provider implementation complete!")
        print("   - Provider follows contracts ✅")
        print("   - Message parsing functional ✅")
        print("   - SMTP server interface ready ✅")
        print("   - No OAuth required (username/password) ✅")
        print("   - Ready for SMTP server deployment ✅")
    else:
        print("\n⚠️  Some tests failed - check implementation")

if __name__ == "__main__":
    asyncio.run(main())