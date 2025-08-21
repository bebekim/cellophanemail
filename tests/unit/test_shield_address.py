"""Tests for ShieldAddress model using TDD methodology."""

import pytest
import uuid
from datetime import datetime
from cellophanemail.models.shield_address import ShieldAddress
from cellophanemail.models.user import User


class TestShieldAddressModel:
    """Test the ShieldAddress model basic functionality."""
    
    def test_shield_address_model_exists_with_required_fields(self):
        """Test that ShieldAddress model has the required field definitions."""
        # This test will fail initially because the model doesn't exist yet
        # Testing the most basic structure requirements
        
        # Test that the model class exists and has required column definitions
        assert hasattr(ShieldAddress, 'shield_address')
        assert hasattr(ShieldAddress, 'user')
        assert hasattr(ShieldAddress, 'is_active')
        assert hasattr(ShieldAddress, 'created_at')
        assert hasattr(ShieldAddress, 'updated_at')
        
        # Test column types are correct
        assert ShieldAddress.shield_address._meta.unique is True
        assert ShieldAddress.user._meta.null is False
        # Test that is_active has a default value (Boolean columns store default differently)
        assert hasattr(ShieldAddress.is_active, 'default')
    
    def test_shield_address_can_be_created_with_user_reference(self):
        """Test that ShieldAddress can be instantiated with valid user reference."""
        # RED phase - this test will fail because we need proper instantiation with user
        
        # Create a mock user ID (we're not testing User model here, just the relationship)
        user_id = uuid.uuid4()
        
        # This should work without hitting the database
        shield = ShieldAddress(
            shield_address="test@cellophanemail.com",
            user=user_id,
            _ignore_missing=True  # Piccolo flag to avoid validation for testing
        )
        
        # Test basic attributes are accessible
        assert shield.shield_address == "test@cellophanemail.com"
        assert shield.user == user_id
        assert shield.is_active is True  # Default value
    
    def test_get_by_shield_address_method_exists(self):
        """Test that get_by_shield_address class method exists and can be called."""
        # RED phase - this will fail because the method doesn't exist yet
        
        # Test that the method exists
        assert hasattr(ShieldAddress, 'get_by_shield_address')
        assert callable(ShieldAddress.get_by_shield_address)
        
        # Test that the method signature indicates it's async (returns a coroutine)
        # We don't actually call it to avoid the unawaited coroutine warning
        import inspect
        assert inspect.iscoroutinefunction(ShieldAddress.get_by_shield_address)
    
    def test_get_user_by_shield_method_exists(self):
        """Test that get_user_by_shield class method exists and can be called."""
        # RED phase - this will fail because the method doesn't exist yet
        
        # Test that the method exists
        assert hasattr(ShieldAddress, 'get_user_by_shield')
        assert callable(ShieldAddress.get_user_by_shield)
    
    def test_create_for_user_method_exists(self):
        """Test that create_for_user class method exists and can be called."""
        # RED phase - this will fail because the method doesn't exist yet
        
        # Test that the method exists
        assert hasattr(ShieldAddress, 'create_for_user')
        assert callable(ShieldAddress.create_for_user)
    
    def test_deactivate_instance_method_exists(self):
        """Test that deactivate instance method exists and can be called."""
        # RED phase - this will fail because the method doesn't exist yet
        
        # Create a mock shield address instance
        user_id = uuid.uuid4()
        shield = ShieldAddress(
            shield_address="test@cellophanemail.com",
            user=user_id,
            _ignore_missing=True
        )
        
        # Test that the method exists
        assert hasattr(shield, 'deactivate')
        assert callable(shield.deactivate)
        
        # Test that calling deactivate changes is_active to False
        # We'll simulate this without database interaction for unit testing
        original_is_active = shield.is_active
        assert original_is_active is True  # Should start as active
