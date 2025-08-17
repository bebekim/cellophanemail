"""Tests for authentication service functions."""

import pytest
import pytest_asyncio
from src.cellophanemail.services.auth_service import (
    hash_password, 
    verify_password, 
    generate_shield_username, 
    generate_verification_token,
    validate_email_unique,
    create_user
)
from src.cellophanemail.models.user import User
from unittest.mock import AsyncMock, MagicMock, patch


class TestHashPassword:
    """Test password hashing functionality."""
    
    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "test_password_123"
        result = hash_password(password)
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def test_hash_password_different_for_same_input(self):
        """Test that hash_password returns different hashes for same input (due to salt)."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Due to bcrypt salt, hashes should be different
        assert hash1 != hash2
        
    def test_hash_password_starts_with_bcrypt_prefix(self):
        """Test that hash_password returns bcrypt hash format."""
        password = "test_password_123"
        result = hash_password(password)
        
        # Bcrypt hashes start with $2b$
        assert result.startswith("$2b$")


class TestVerifyPassword:
    """Test password verification functionality."""
    
    def test_verify_password_correct_password_returns_true(self):
        """Test that verify_password returns True for correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        result = verify_password(password, hashed)
        assert result is True
        
    def test_verify_password_incorrect_password_returns_false(self):
        """Test that verify_password returns False for incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        result = verify_password(wrong_password, hashed)
        assert result is False
        
    def test_verify_password_empty_password_returns_false(self):
        """Test that verify_password returns False for empty password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        result = verify_password("", hashed)
        assert result is False


class TestGenerateShieldUsername:
    """Test shield username generation functionality."""
    
    def test_generate_shield_username_returns_string(self):
        """Test that generate_shield_username returns a string."""
        email = "test@example.com"
        result = generate_shield_username(email)
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def test_generate_shield_username_contains_email_part(self):
        """Test that generate_shield_username contains part of the email."""
        email = "john.doe@example.com"
        result = generate_shield_username(email)
        
        # Should contain "john" or "johndoe" or similar
        assert "john" in result.lower()
        
    def test_generate_shield_username_has_numbers(self):
        """Test that generate_shield_username includes numbers for uniqueness."""
        email = "test@example.com"
        result = generate_shield_username(email)
        
        # Should contain at least one digit
        assert any(char.isdigit() for char in result)
        
    def test_generate_shield_username_different_emails_different_results(self):
        """Test that different emails generate different usernames."""
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        
        result1 = generate_shield_username(email1)
        result2 = generate_shield_username(email2)
        
        assert result1 != result2


class TestGenerateVerificationToken:
    """Test verification token generation functionality."""
    
    def test_generate_verification_token_returns_string(self):
        """Test that generate_verification_token returns a string."""
        result = generate_verification_token()
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def test_generate_verification_token_sufficient_length(self):
        """Test that generate_verification_token returns sufficiently long token."""
        result = generate_verification_token()
        
        # Should be at least 32 characters for security
        assert len(result) >= 32
        
    def test_generate_verification_token_different_each_time(self):
        """Test that generate_verification_token returns different tokens each time."""
        token1 = generate_verification_token()
        token2 = generate_verification_token()
        
        assert token1 != token2
        
    def test_generate_verification_token_alphanumeric(self):
        """Test that generate_verification_token returns alphanumeric characters."""
        result = generate_verification_token()
        
        # Should only contain alphanumeric characters (and possibly hyphens if UUID)
        assert all(c.isalnum() or c == '-' for c in result)


class TestValidateEmailUnique:
    """Test email uniqueness validation functionality."""
    
    @pytest.mark.asyncio
    async def test_validate_email_unique_returns_true_when_not_exists(self):
        """Test that validate_email_unique returns True when email doesn't exist."""
        with patch('src.cellophanemail.services.auth_service.User') as MockUser:
            mock_run = AsyncMock(return_value=False)
            MockUser.exists.return_value.where.return_value.run = mock_run
            
            result = await validate_email_unique("new@example.com")
            assert result is True
            
    @pytest.mark.asyncio
    async def test_validate_email_unique_returns_false_when_exists(self):
        """Test that validate_email_unique returns False when email exists."""
        with patch('src.cellophanemail.services.auth_service.User') as MockUser:
            mock_run = AsyncMock(return_value=True)
            MockUser.exists.return_value.where.return_value.run = mock_run
            
            result = await validate_email_unique("existing@example.com")
            assert result is False


class TestCreateUser:
    """Test user creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user_creates_user_with_correct_data(self):
        """Test that create_user creates a user with all provided data."""
        with patch('src.cellophanemail.services.auth_service.User') as MockUser:
            mock_user = MagicMock()
            mock_save = MagicMock()
            mock_save.run = AsyncMock()
            mock_user.save.return_value = mock_save
            MockUser.return_value = mock_user
            
            user_data = {
                "email": "test@example.com",
                "password": "plaintext123",
                "first_name": "Test",
                "last_name": "User"
            }
            
            result = await create_user(**user_data)
            
            # Verify user was created with correct data
            MockUser.assert_called_once()
            # Check the kwargs passed to User constructor
            call_kwargs = MockUser.call_args.kwargs
            assert call_kwargs['email'] == "test@example.com"
            # Password should be hashed (using correct field name)
            assert call_kwargs['hashed_password'] != "plaintext123"
            assert call_kwargs['hashed_password'].startswith("$2b$")
            
    @pytest.mark.asyncio 
    async def test_create_user_generates_shield_address(self):
        """Test that create_user generates a shield address."""
        with patch('src.cellophanemail.services.auth_service.User') as MockUser:
            mock_user = MagicMock()
            mock_save = MagicMock()
            mock_save.run = AsyncMock()
            mock_user.save.return_value = mock_save
            MockUser.return_value = mock_user
            
            user_data = {
                "email": "test@example.com",
                "password": "plaintext123",
                "first_name": "Test",
                "last_name": "User"
            }
            
            result = await create_user(**user_data)
            
            # Verify shield username was generated (using correct field name)
            call_kwargs = MockUser.call_args.kwargs
            assert call_kwargs['username'] is not None
            assert isinstance(call_kwargs['username'], str)
            assert len(call_kwargs['username']) > 0
            
    @pytest.mark.asyncio
    async def test_create_user_generates_verification_token(self):
        """Test that create_user generates a verification token."""
        with patch('src.cellophanemail.services.auth_service.User') as MockUser:
            mock_user = MagicMock()
            mock_save = MagicMock()
            mock_save.run = AsyncMock()
            mock_user.save.return_value = mock_save
            MockUser.return_value = mock_user
            
            user_data = {
                "email": "test@example.com",
                "password": "plaintext123",
                "first_name": "Test",
                "last_name": "User"
            }
            
            result = await create_user(**user_data)
            
            # Verify verification token was generated
            call_kwargs = MockUser.call_args.kwargs
            assert call_kwargs['email_verification_token'] is not None
            assert isinstance(call_kwargs['email_verification_token'], str)
            assert len(call_kwargs['email_verification_token']) >= 32