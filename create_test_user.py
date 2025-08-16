#!/usr/bin/env python3
"""Create a test user with shield address for webhook testing."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cellophanemail.services.user_service import UserService


async def create_test_user():
    """Create a test user with shield address."""
    try:
        print("Creating test user with shield address...")
        
        # Create user with shield (use unique email)
        import uuid
        unique_email = f"testuser{uuid.uuid4().hex[:8]}@gmail.com"
        
        user, shield = await UserService.create_user_with_shield(
            email=unique_email,
            password_hash="fake-hash-for-testing",
            first_name="Test",
            last_name="User"
        )
        
        print(f"✅ Created user: {user.email} (ID: {user.id})")
        print(f"✅ Shield address: {shield.shield_address}")
        print(f"\n🎯 Use this shield address for testing:")
        print(f"   {shield.shield_address}")
        
        return shield.shield_address
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    shield_address = asyncio.run(create_test_user())
    
    if shield_address:
        print(f"\n📧 Test email command:")
        print(f"curl -X POST http://localhost:8000/webhooks/postmark \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(f'  -d \'{{"From": "test@example.com", "To": "{shield_address}", "Subject": "Test", "MessageID": "test-123", "Date": "2025-08-14T12:00:00Z", "TextBody": "Hello test"}}\'')