"""Test UUID-based shield address generation with TDD methodology."""

import pytest
import uuid
from cellophanemail.models.shield_address import ShieldAddress
from cellophanemail.models.user import User


class TestShieldAddressGeneration:
    """Test UUID-based shield address generation following TDD red-green-refactor cycle."""
    
    def test_generate_uuid_based_shield_address_fails_initially(self):
        """RED PHASE: Test that generates UUID-based shield address - should FAIL initially."""
        # This test defines what we want: a function that generates a UUID-based shield address
        # Format should be: {uuid}@shields.cellophanemail.com
        
        # Expected behavior: given a user, generate a unique shield address
        user_id = str(uuid.uuid4())
        
        # This method doesn't exist yet - TEST SHOULD FAIL
        shield_address = ShieldAddress.generate_uuid_shield(user_id, domain="shields.cellophanemail.com")
        
        # Verify the generated shield address format
        assert shield_address is not None
        assert "@shields.cellophanemail.com" in shield_address
        
        # Verify it contains a UUID (32 chars without hyphens)
        local_part = shield_address.split("@")[0]
        assert len(local_part) == 32  # UUID format without hyphens: 32 hex characters
        
        # Verify it's a valid UUID format (add hyphens back for validation)
        # Convert 32-char hex to standard UUID format
        formatted_uuid = f"{local_part[:8]}-{local_part[8:12]}-{local_part[12:16]}-{local_part[16:20]}-{local_part[20:]}"
        uuid.UUID(formatted_uuid)  # This will throw if not valid UUID format
    
    def test_user_signup_creates_shield_address_automatically(self):
        """RED PHASE: Test that user signup automatically creates shield address - should FAIL initially."""
        # This test defines the integration: when a user signs up, they should get a shield address
        
        user_id = str(uuid.uuid4())
        user_email = "newuser@example.com" 
        
        # This method doesn't exist yet - TEST SHOULD FAIL
        # We want a method that creates both user record and shield address atomically
        shield_address = ShieldAddress.create_shield_for_new_user(
            user_id=user_id,
            user_email=user_email,
            shield_domain="shields.cellophanemail.com"
        )
        
        # Verify shield address was created 
        assert shield_address is not None
        assert "@shields.cellophanemail.com" in shield_address
        
        # Verify it contains a UUID in the local part (32 chars without hyphens)
        local_part = shield_address.split("@")[0]
        assert len(local_part) == 32  # UUID without hyphens
        # Convert back to standard UUID format for validation
        formatted_uuid = f"{local_part[:8]}-{local_part[8:12]}-{local_part[12:16]}-{local_part[16:20]}-{local_part[20:]}"
        uuid.UUID(formatted_uuid)  # Should be valid UUID format
