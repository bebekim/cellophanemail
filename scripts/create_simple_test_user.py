#!/usr/bin/env python3
"""Create a test user with a simple shield address for testing."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Setup Django-style settings for Piccolo
os.environ.setdefault('PICCOLO_CONF', 'piccolo_conf')

from piccolo.apps.user.tables import BaseUser
from cellophanemail.models.user import User
from cellophanemail.models.shield_address import ShieldAddress


async def create_simple_test_user():
    """Create a test user with simple shield address."""
    
    test_email = "goldenfermi@gmail.com"  # Your real email (where cleaned emails go)
    shield_email = "goldenfermi.test@cellophanemail.com"  # Shield address for testing
    
    try:
        # Check if user already exists
        existing_user = await User.select().where(
            User.email == test_email
        ).first()
        
        if existing_user:
            print(f"✓ User already exists: {test_email}")
            user = existing_user
        else:
            # Create new user
            user = User(
                email=test_email,
                password_hash="test-hash",
                first_name="Golden",
                last_name="Fermi"
            )
            await user.save()
            print(f"✅ Created user: {test_email}")
        
        # Check if shield address already exists
        existing_shield = await ShieldAddress.select().where(
            ShieldAddress.shield_address == shield_email
        ).first()
        
        if existing_shield:
            # Update to point to our user
            existing_shield.user = user.id
            existing_shield.is_active = True
            await existing_shield.save()
            print(f"✓ Updated existing shield: {shield_email}")
        else:
            # Create shield address
            shield = ShieldAddress(
                shield_address=shield_email,
                user=user.id,
                is_active=True
            )
            await shield.save()
            print(f"✅ Created shield: {shield_email}")
        
        print(f"\n🎯 Test Setup Complete!")
        print(f"   Your real email: {test_email}")
        print(f"   Shield address: {shield_email}")
        print(f"\n📧 To test:")
        print(f"   Send an email to: {shield_email}")
        print(f"   It will be processed and forwarded to: {test_email}")
        
        return shield_email
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    shield = asyncio.run(create_simple_test_user())
    
    if shield:
        print(f"\n🧪 Test now:")
        print(f"   1. Send email to: {shield}")
        print(f"   2. Watch the app logs for processing")
        print(f"   3. Check your inbox at goldenfermi@gmail.com")