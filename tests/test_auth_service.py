"""Tests for authentication service functions."""

import pytest
import pytest_asyncio
from cellophanemail.services.auth_service import (
    hash_password, 
    verify_password, 
    generate_shield_username, 
    generate_verification_token,
    validate_email_unique,
    create_user
)
from cellophanemail.models.user import User
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
        with patch('cellophanemail.services.auth_service.User') as MockUser:
            mock_run = AsyncMock(return_value=False)
            MockUser.exists.return_value.where.return_value.run = mock_run
            
            result = await validate_email_unique("new@example.com")
            assert result is True
            
    @pytest.mark.asyncio
    async def test_validate_email_unique_returns_false_when_exists(self):
        """Test that validate_email_unique returns False when email exists."""
        with patch('cellophanemail.services.auth_service.User') as MockUser:
            mock_run = AsyncMock(return_value=True)
            MockUser.exists.return_value.where.return_value.run = mock_run
            
            result = await validate_email_unique("existing@example.com")
            assert result is False


class TestCreateUser:
    """Test user creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user_creates_user_with_correct_data(self):
        """Test that create_user creates a user with all provided data."""
        with patch('cellophanemail.services.auth_service.User') as MockUser:
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
        with patch('cellophanemail.services.auth_service.User') as MockUser:
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
        with patch('cellophanemail.services.auth_service.User') as MockUser:
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
            assert call_kwargs['verification_token'] is not None
            assert isinstance(call_kwargs['verification_token'], str)
            assert len(call_kwargs['verification_token']) >= 32


class TestOAuthUserCreation:
    """Test OAuth user creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user_from_oauth_profile_creates_user_with_google_data(self):
        """Test that create_user_from_oauth_profile creates user from Google OAuth data."""
        # Import the function we're about to implement (this will fail initially)
        from cellophanemail.services.auth_service import create_user_from_oauth_profile
        
        # Mock Google OAuth profile data
        oauth_profile = {
            "email": "john.doe@gmail.com",
            "given_name": "John",
            "family_name": "Doe",
            "picture": "https://lh3.googleusercontent.com/user/photo.jpg",
            "sub": "google_user_id_12345",
            "email_verified": True
        }
        
        with patch('cellophanemail.services.auth_service.User') as MockUser:
            mock_user = MagicMock()
            mock_save = MagicMock()
            mock_save.run = AsyncMock()
            mock_user.save.return_value = mock_save
            MockUser.return_value = mock_user
            
            # Call the function we're testing
            result = await create_user_from_oauth_profile(oauth_profile, provider="google")
            
            # Verify user was created with OAuth data
            MockUser.assert_called_once()
            call_kwargs = MockUser.call_args.kwargs
            
            # Check email and names from OAuth profile
            assert call_kwargs['email'] == "john.doe@gmail.com"
            assert call_kwargs['first_name'] == "John"
            assert call_kwargs['last_name'] == "Doe"
            
            # OAuth users should not have a password (OAuth-only accounts)
            assert call_kwargs['hashed_password'] is None
            
            # Should be verified if email is verified by OAuth provider
            assert call_kwargs['is_verified'] is True
            
            # Should still generate shield username
            assert call_kwargs['username'] is not None
            assert isinstance(call_kwargs['username'], str)
            
            # Should save the user
            mock_user.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_from_oauth_profile_raises_error_without_email(self):
        """Test that create_user_from_oauth_profile raises ValueError when email is missing."""
        from cellophanemail.services.auth_service import create_user_from_oauth_profile
        
        # OAuth profile without email
        oauth_profile = {
            "given_name": "John",
            "family_name": "Doe", 
            "picture": "https://lh3.googleusercontent.com/user/photo.jpg",
            "sub": "google_user_id_12345"
        }
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="OAuth profile must contain an email address"):
            await create_user_from_oauth_profile(oauth_profile, provider="google")


class TestOAuthService:
    """Test OAuth service functionality for handling provider callbacks."""
    
    @pytest.mark.asyncio
    async def test_handle_google_callback_exchanges_code_for_profile(self):
        """Test that handle_google_callback exchanges auth code for user profile."""
        # Import the function we're about to implement (this will fail initially)
        from cellophanemail.services.auth_service import handle_google_oauth_callback
        
        auth_code = "google_auth_code_12345"
        expected_profile = {
            "email": "test@gmail.com",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://lh3.googleusercontent.com/user/photo.jpg",
            "sub": "google_user_id_67890",
            "email_verified": True
        }
        
        # Mock the Google OAuth token exchange and profile fetch
        with patch('cellophanemail.services.auth_service.fetch_google_user_profile') as mock_fetch:
            mock_fetch.return_value = expected_profile
            
            # Call the function we're testing
            result = await handle_google_oauth_callback(auth_code)
            
            # Should return the user profile data
            assert result == expected_profile
            
            # Should have called the Google API with the auth code
            mock_fetch.assert_called_once_with(auth_code)
    
    @pytest.mark.asyncio  
    async def test_fetch_google_user_profile_makes_http_request(self):
        """Test that fetch_google_user_profile makes HTTP request to Google API."""
        from cellophanemail.services.auth_service import fetch_google_user_profile
        
        auth_code = "real_auth_code_123"
        
        # Mock HTTP client for Google OAuth API calls
        with patch('cellophanemail.services.auth_service.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "google_access_token_123",
                "token_type": "Bearer",
                "expires_in": 3600
            }
            
            mock_profile_response = MagicMock()
            mock_profile_response.json.return_value = {
                "email": "real@gmail.com",
                "given_name": "Real",
                "family_name": "User",
                "picture": "https://lh3.googleusercontent.com/real/photo.jpg",
                "sub": "real_google_id_123",
                "email_verified": True
            }
            
            # Configure mock to return different responses for token and profile endpoints
            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.get.return_value = mock_profile_response
            
            # Call the function
            result = await fetch_google_user_profile(auth_code)
            
            # Should make POST request to exchange code for token
            mock_client_instance.post.assert_called_once()
            post_call = mock_client_instance.post.call_args
            assert "token" in post_call[0][0]  # URL should contain token endpoint
            
            # Should make GET request to fetch profile with token
            mock_client_instance.get.assert_called_once()
            get_call = mock_client_instance.get.call_args  
            assert "userinfo" in get_call[0][0]  # URL should contain userinfo endpoint
            
            # Should return the profile data
            assert result["email"] == "real@gmail.com"


class TestOAuthUserFields:
    """Test OAuth-specific user fields and functionality."""
    
    @pytest.mark.asyncio
    async def test_user_model_supports_oauth_fields(self):
        """Test that User model has OAuth provider and oauth_id fields."""
        from cellophanemail.models.user import User
        
        # RED PHASE - This test will fail because oauth_provider and oauth_id fields don't exist yet
        user = User(
            email="oauth.user@gmail.com",
            first_name="OAuth",
            last_name="User",
            oauth_provider="google",  # This field doesn't exist yet - should fail
            oauth_id="google_123456789",  # This field doesn't exist yet - should fail
            hashed_password=None,  # OAuth users have no password
            is_verified=True
        )
        
        # Verify the fields exist and have correct values
        assert user.oauth_provider == "google"
        assert user.oauth_id == "google_123456789"
        assert user.hashed_password is None
        assert user.is_verified is True
    
    @pytest.mark.asyncio
    async def test_find_existing_user_by_email_and_oauth(self):
        """Test function to find existing user by email and optionally link OAuth."""
        from cellophanemail.services.auth_service import find_or_link_oauth_user
        
        # RED PHASE - This function doesn't exist yet, should fail
        oauth_profile = {
            "email": "existing@example.com",
            "sub": "google_12345",
            "given_name": "Existing",
            "family_name": "User",
            "email_verified": True
        }
        
        # Test case 1: No existing user - should return None
        with patch('cellophanemail.services.auth_service.User') as MockUser:
            MockUser.select.return_value.where.return_value.first = AsyncMock(return_value=None)
            
            result = await find_or_link_oauth_user(oauth_profile, "google")
            assert result is None
        
        # Test case 2: Existing user without OAuth - should link OAuth and return user
        with patch('cellophanemail.services.auth_service.User') as MockUser:
            mock_existing_user = MagicMock()
            mock_existing_user.oauth_provider = None
            mock_existing_user.oauth_id = None
            mock_existing_user.email = "existing@example.com"
            mock_save = MagicMock()
            mock_save.run = AsyncMock()
            mock_existing_user.save.return_value = mock_save
            
            MockUser.select.return_value.where.return_value.first = AsyncMock(return_value=mock_existing_user)
            
            result = await find_or_link_oauth_user(oauth_profile, "google")
            
            # Should link OAuth to existing user
            assert mock_existing_user.oauth_provider == "google"
            assert mock_existing_user.oauth_id == "google_12345"
            mock_existing_user.save.assert_called_once()
            assert result == mock_existing_user