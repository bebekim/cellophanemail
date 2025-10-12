"""Tests for configuration security validation."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch
from cellophanemail.config.settings import Settings
from cellophanemail.app import validate_configuration


class TestSettingsValidation:
    """Test Pydantic field validation in Settings class."""

    def test_secret_key_validation_empty_fails(self):
        """Test that empty secret key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                secret_key="",
                database_url="postgresql://user:secure_pass@localhost:5432/test",
                anthropic_api_key="sk-ant-api03-valid-key-here-abcdefghijklmnop1234567890123456789012345"
            )
        assert "SECRET_KEY is required" in str(exc_info.value)

    def test_secret_key_validation_too_short_fails(self):
        """Test that short secret key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                secret_key="short",
                database_url="postgresql://user:secure_pass@localhost:5432/test",
                anthropic_api_key="sk-ant-api03-valid-key-here-abcdefghijklmnop1234567890123456789012345"
            )
        assert "must be at least 32 characters" in str(exc_info.value)

    def test_secret_key_validation_default_fails(self):
        """Test that default secret key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                secret_key="dev-secret-key-change-in-production",
                database_url="postgresql://user:secure_pass@localhost:5432/test",
                anthropic_api_key="sk-ant-api03-valid-key-here-abcdefghijklmnop1234567890123456789012345"
            )
        assert "Default SECRET_KEY is not allowed" in str(exc_info.value)

    def test_secret_key_validation_character_variety_fails(self):
        """Test that secret keys with insufficient character variety fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                secret_key="a" * 32,  # 32 chars but all the same character
                database_url="postgresql://user:secure_pass@localhost:5432/test",
                anthropic_api_key="sk-ant-api03-valid-key-here-abcdefghijklmnop1234567890123456789012345"
            )
        assert "character variety" in str(exc_info.value)

    def test_database_url_validation_default_password_fails(self):
        """Test that database URL with default password fails."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                secret_key="a-secure-32-character-secret-key-12345",
                database_url="postgresql://postgres:password@localhost:5432/test",
                anthropic_api_key="sk-ant-api03-valid-key-here-abcdefghijklmnop1234567890123456789012345"
            )
        assert "default 'password'" in str(exc_info.value)

    def test_anthropic_api_key_validation_empty_fails(self):
        """Test that empty Anthropic API key fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                secret_key="a-secure-32-character-secret-key-12345",
                database_url="postgresql://user:secure_pass@localhost:5432/test",
                anthropic_api_key=""
            )
        assert "ANTHROPIC_API_KEY is required" in str(exc_info.value)

    def test_anthropic_api_key_validation_invalid_format_fails(self):
        """Test that invalid Anthropic API key format fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                secret_key="a-secure-32-character-secret-key-12345",
                database_url="postgresql://user:secure_pass@localhost:5432/test",
                anthropic_api_key="invalid-key-format"
            )
        assert "must be a valid Anthropic API key format" in str(exc_info.value)

    def test_valid_configuration_passes(self):
        """Test that valid configuration passes all validations."""
        settings = Settings(
            secret_key="a-very-secure-32-character-secret-key-123456789",
            database_url="postgresql://user:secure_password_123@localhost:5432/cellophanemail",
            anthropic_api_key="sk-ant-api03-valid-key-here-abcdefghijklmnop1234567890123456789012345"
        )
        assert settings.secret_key == "a-very-secure-32-character-secret-key-123456789"
        assert "secure_password_123" in settings.database_url


class TestAppConfigValidation:
    """Test application-level configuration validation."""

    def test_production_validation_missing_encryption_key(self):
        """Test production validation fails with missing encryption key."""
        # Mock settings for production
        mock_settings = type('Settings', (), {
            'is_production': True,
            'encryption_key': '',
            'ai_provider': 'anthropic',
            'anthropic_api_key': 'sk-ant-api03-key',
            'email_delivery_method': 'smtp',
            'email_password': 'password123',
            'secret_key': 'valid-secret-key',
            'database_url': 'postgresql://user:securepass@localhost:5432/db'
        })()

        with pytest.raises(ValueError) as exc_info:
            validate_configuration(mock_settings)
        assert "ENCRYPTION_KEY is required in production" in str(exc_info.value)

    def test_production_validation_missing_api_key(self):
        """Test production validation fails with missing API key."""
        mock_settings = type('Settings', (), {
            'is_production': True,
            'encryption_key': 'valid-encryption-key',
            'ai_provider': 'anthropic',
            'anthropic_api_key': '',
            'email_delivery_method': 'smtp',
            'email_password': 'password123',
            'secret_key': 'valid-secret-key',
            'database_url': 'postgresql://user:securepass@localhost:5432/db'
        })()

        with pytest.raises(ValueError) as exc_info:
            validate_configuration(mock_settings)
        assert "ANTHROPIC_API_KEY is required" in str(exc_info.value)

    def test_database_password_validation(self):
        """Test database password validation catches default passwords."""
        mock_settings = type('Settings', (), {
            'is_production': False,
            'secret_key': 'valid-secret-key-32-characters-long',
            'database_url': 'postgresql://postgres:password@localhost:5432/db'
        })()

        with pytest.raises(ValueError) as exc_info:
            validate_configuration(mock_settings)
        assert "default password" in str(exc_info.value)

    def test_valid_production_configuration_passes(self):
        """Test that valid production configuration passes validation."""
        mock_settings = type('Settings', (), {
            'is_production': True,
            'encryption_key': 'valid-encryption-key-32-chars-long',
            'ai_provider': 'anthropic',
            'anthropic_api_key': 'sk-ant-api03-valid-key',
            'email_delivery_method': 'postmark',
            'postmark_api_token': 'valid-postmark-token',
            'secret_key': 'valid-secret-key-32-characters-long',
            'database_url': 'postgresql://user:secure_db_pass@localhost:5432/db'
        })()

        # Should not raise any exceptions
        validate_configuration(mock_settings)

    def test_development_configuration_warns_about_default_key(self):
        """Test development configuration warns about default keys."""
        mock_settings = type('Settings', (), {
            'is_production': False,
            'secret_key': 'dev-secret-key-change-in-production',
            'database_url': 'postgresql://user:secure_password@localhost:5432/db'
        })()

        with pytest.raises(ValueError) as exc_info:
            validate_configuration(mock_settings)
        assert "Default SECRET_KEY detected" in str(exc_info.value)