#!/usr/bin/env python3
"""Create a test user with a specific shield address for testing."""

import asyncio
import sys
from cellophanemail.models.user import User
from cellophanemail.services.auth_service import hash_password
import uuid


async def create_test_user_with_shield(shield_username: str, email: str = None):
    """Create a test user with a specific shield username."""
    if email is None:
        email = f"test_{shield_username}@example.com"
    
    # Check if user with this shield username already exists
    existing = await User.select().where(User.username == shield_username).first()
    if existing:
        print(f"✅ User with shield {shield_username}@cellophanemail.com already exists")
        return existing
    
    # Create new user
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=shield_username,
        hashed_password=hash_password("TestPass123!"),
        first_name="Test",
        last_name="User",
        is_verified=True,  # Mark as verified for testing
        is_active=True
    )
    
    await user.save()
    print(f"✅ Created test user:")
    print(f"   Email: {email}")
    print(f"   Shield: {shield_username}@cellophanemail.com")
    print(f"   Password: TestPass123!")
    
    return user


async def main():
    """Create common test users."""
    # Create the test user that the webhook tests expect
    await create_test_user_with_shield(
        "c5b8bec80d4046139e94176626b923d6",
        "webhook-test@example.com"
    )
    
    # Create a more friendly test user
    await create_test_user_with_shield(
        "testuser123",
        "testuser@example.com"
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Allow creating specific shield username from command line
        shield = sys.argv[1]
        email = sys.argv[2] if len(sys.argv) > 2 else None
        asyncio.run(create_test_user_with_shield(shield, email))
    else:
        asyncio.run(main())