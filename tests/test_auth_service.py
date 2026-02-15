"""Tests for authentication service functions."""

import pytest
from cellophanemail.services.auth_service import (
    hash_password,
    verify_password,
    generate_shield_username,
    generate_verification_token,
    validate_email_unique,
    validate_phone_unique,
    validate_phone_format,
    detect_identifier_type,
    create_user,
)
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

    def test_generate_shield_username_uses_secure_random(self):
        """Test that generate_shield_username uses cryptographically secure random generation."""
        with patch(
            "cellophanemail.services.auth_service.secrets.randbelow"
        ) as mock_secrets:
            mock_secrets.return_value = 500  # This will result in 600 (500 + 100)

            email = "test@example.com"
            username = generate_shield_username(email, "email")

            # Verify secrets.randbelow was called with correct parameter
            mock_secrets.assert_called_once_with(900)

            # Verify the username contains the expected number
            assert "test600" == username

    def test_generate_shield_username_from_phone(self):
        """Test shield username generation from phone number."""
        phone = "+61412345678"
        result = generate_shield_username(phone, "phone")

        assert isinstance(result, str)
        assert "user5678" in result  # last 4 digits
        assert any(char.isdigit() for char in result)

    def test_generate_shield_username_secure_random_range(self):
        """Test that secure random generation produces numbers in correct range."""
        email = "test@example.com"

        # Generate multiple usernames to check range
        for _ in range(100):
            username = generate_shield_username(email)
            # Extract the number from the end
            number_part = "".join(filter(str.isdigit, username[-3:]))
            number = int(number_part) if number_part else 0

            # Should be in range 100-999
            assert 100 <= number <= 999


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
        assert all(c.isalnum() or c == "-" for c in result)


class TestValidateEmailUnique:
    """Test email uniqueness validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_email_unique_returns_true_when_not_exists(self):
        """Test that validate_email_unique returns True when email doesn't exist."""
        with patch("cellophanemail.services.auth_service.User") as MockUser:
            mock_run = AsyncMock(return_value=False)
            MockUser.exists.return_value.where.return_value.run = mock_run

            result = await validate_email_unique("new@example.com")
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_email_unique_returns_false_when_exists(self):
        """Test that validate_email_unique returns False when email exists."""
        with patch("cellophanemail.services.auth_service.User") as MockUser:
            mock_run = AsyncMock(return_value=True)
            MockUser.exists.return_value.where.return_value.run = mock_run

            result = await validate_email_unique("existing@example.com")
            assert result is False


class TestCreateUser:
    """Test user creation functionality."""

    @pytest.mark.asyncio
    async def test_create_user_with_email(self):
        """Test that create_user creates a user with email."""
        with patch("cellophanemail.services.auth_service.User") as MockUser:
            mock_user = MagicMock()
            mock_save = MagicMock()
            mock_save.run = AsyncMock()
            mock_user.save.return_value = mock_save
            MockUser.return_value = mock_user

            await create_user(
                password="plaintext123",
                email="test@example.com",
                first_name="Test",
                last_name="User",
            )

            MockUser.assert_called_once()
            call_kwargs = MockUser.call_args.kwargs
            assert call_kwargs["email"] == "test@example.com"
            assert call_kwargs["phone_number"] is None
            assert call_kwargs["verification_method"] == "email"
            assert call_kwargs["hashed_password"] != "plaintext123"
            assert call_kwargs["hashed_password"].startswith("$2b$")

    @pytest.mark.asyncio
    async def test_create_user_with_phone(self):
        """Test that create_user creates a user with phone number."""
        with patch("cellophanemail.services.auth_service.User") as MockUser:
            mock_user = MagicMock()
            mock_save = MagicMock()
            mock_save.run = AsyncMock()
            mock_user.save.return_value = mock_save
            MockUser.return_value = mock_user

            await create_user(
                password="plaintext123",
                phone_number="+61412345678",
            )

            MockUser.assert_called_once()
            call_kwargs = MockUser.call_args.kwargs
            assert call_kwargs["email"] is None
            assert call_kwargs["phone_number"] == "+61412345678"
            assert call_kwargs["verification_method"] == "phone"

    @pytest.mark.asyncio
    async def test_create_user_generates_shield_address(self):
        """Test that create_user generates a shield address."""
        with patch("cellophanemail.services.auth_service.User") as MockUser:
            mock_user = MagicMock()
            mock_save = MagicMock()
            mock_save.run = AsyncMock()
            mock_user.save.return_value = mock_save
            MockUser.return_value = mock_user

            await create_user(
                password="plaintext123",
                email="test@example.com",
            )

            call_kwargs = MockUser.call_args.kwargs
            assert call_kwargs["username"] is not None
            assert isinstance(call_kwargs["username"], str)
            assert len(call_kwargs["username"]) > 0

    @pytest.mark.asyncio
    async def test_create_user_generates_verification_token(self):
        """Test that create_user generates a verification token."""
        with patch("cellophanemail.services.auth_service.User") as MockUser:
            mock_user = MagicMock()
            mock_save = MagicMock()
            mock_save.run = AsyncMock()
            mock_user.save.return_value = mock_save
            MockUser.return_value = mock_user

            await create_user(
                password="plaintext123",
                email="test@example.com",
            )

            call_kwargs = MockUser.call_args.kwargs
            assert call_kwargs["verification_token"] is not None
            assert isinstance(call_kwargs["verification_token"], str)
            assert len(call_kwargs["verification_token"]) >= 32


class TestPhoneValidation:
    """Test phone number validation utilities."""

    def test_valid_phone_format(self):
        assert validate_phone_format("+61412345678") is True
        assert validate_phone_format("+1234567890") is True

    def test_invalid_phone_format(self):
        assert validate_phone_format("0412345678") is False
        assert validate_phone_format("+0123456") is False
        assert validate_phone_format("not-a-phone") is False

    def test_detect_email_identifier(self):
        assert detect_identifier_type("user@example.com") == "email"

    def test_detect_phone_identifier(self):
        assert detect_identifier_type("+61412345678") == "phone"

    @pytest.mark.asyncio
    async def test_validate_phone_unique_true(self):
        with patch("cellophanemail.services.auth_service.User") as MockUser:
            mock_run = AsyncMock(return_value=False)
            MockUser.exists.return_value.where.return_value.run = mock_run
            result = await validate_phone_unique("+61412345678")
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_phone_unique_false(self):
        with patch("cellophanemail.services.auth_service.User") as MockUser:
            mock_run = AsyncMock(return_value=True)
            MockUser.exists.return_value.where.return_value.run = mock_run
            result = await validate_phone_unique("+61412345678")
            assert result is False
