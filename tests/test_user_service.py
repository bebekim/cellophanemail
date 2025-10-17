"""Tests for user service and shield address management."""

import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from cellophanemail.services.user_service import (
    UserService,
    ShieldAddressService
)
from cellophanemail.models.user import User, SubscriptionStatus
from cellophanemail.models.shield_address import ShieldAddress
from cellophanemail.models.organization import Organization


class TestUserServiceCreateUserWithShield:
    """Test UserService.create_user_with_shield method."""

    @pytest.mark.asyncio
    async def test_create_user_with_shield_success(self):
        """Test successful user creation with shield address."""
        email = "newuser@example.com"
        password_hash = "hashed_password_123"

        # Mock User.select().where().first() to return None (no existing user)
        with patch.object(User, 'select') as mock_select:
            mock_where = AsyncMock()
            mock_where.first = AsyncMock(return_value=None)
            mock_select.return_value.where.return_value = mock_where

            # Mock User.save()
            with patch.object(User, 'save', new_callable=AsyncMock) as mock_save:
                # Mock ShieldAddress.create_for_user()
                mock_shield = MagicMock(spec=ShieldAddress)
                mock_shield.shield_address = "abc123def456@cellophanemail.com"
                mock_shield.user = "user-uuid"

                with patch.object(ShieldAddress, 'create_for_user', new_callable=AsyncMock, return_value=mock_shield):
                    user, shield = await UserService.create_user_with_shield(
                        email=email,
                        password_hash=password_hash,
                        first_name="Test",
                        last_name="User"
                    )

                    # Verify user was created
                    assert user.email == email
                    assert user.hashed_password == password_hash
                    assert user.first_name == "Test"
                    assert user.last_name == "User"
                    assert user.subscription_status == SubscriptionStatus.FREE
                    assert user.is_active is True
                    assert user.is_verified is False

                    # Verify shield address was returned
                    assert shield == mock_shield
                    assert "@cellophanemail.com" in shield.shield_address

                    # Verify save was called
                    mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self):
        """Test user creation fails with duplicate email."""
        email = "existing@example.com"

        # Mock existing user
        existing_user = MagicMock(spec=User)
        existing_user.email = email

        with patch.object(User, 'select') as mock_select:
            mock_where = AsyncMock()
            mock_where.first = AsyncMock(return_value=existing_user)
            mock_select.return_value.where.return_value = mock_where

            with pytest.raises(ValueError, match="already exists"):
                await UserService.create_user_with_shield(
                    email=email,
                    password_hash="hash"
                )

    @pytest.mark.asyncio
    async def test_create_user_with_organization(self):
        """Test user creation with organization assignment."""
        org_id = str(uuid.uuid4())

        # Mock Organization lookup
        mock_org = MagicMock(spec=Organization)
        mock_org.id = org_id
        mock_org.is_active = True

        with patch.object(User, 'select') as mock_user_select:
            # No existing user
            mock_where = AsyncMock()
            mock_where.first = AsyncMock(return_value=None)
            mock_user_select.return_value.where.return_value = mock_where

            with patch.object(Organization, 'select') as mock_org_select:
                # Organization exists and is active
                mock_org_where = AsyncMock()
                mock_org_where.first = AsyncMock(return_value=mock_org)
                mock_org_select.return_value.where.return_value = mock_org_where

                with patch.object(User, 'save', new_callable=AsyncMock):
                    mock_shield = MagicMock(spec=ShieldAddress)
                    mock_shield.shield_address = "test@cellophanemail.com"

                    with patch.object(ShieldAddress, 'create_for_user', new_callable=AsyncMock, return_value=mock_shield):
                        user, shield = await UserService.create_user_with_shield(
                            email="org@example.com",
                            password_hash="hash",
                            organization_id=org_id
                        )

                        assert user.organization == org_id

    @pytest.mark.asyncio
    async def test_create_user_invalid_organization(self):
        """Test user creation fails with invalid organization."""
        org_id = str(uuid.uuid4())

        with patch.object(User, 'select') as mock_user_select:
            mock_where = AsyncMock()
            mock_where.first = AsyncMock(return_value=None)
            mock_user_select.return_value.where.return_value = mock_where

            with patch.object(Organization, 'select') as mock_org_select:
                # Organization not found
                mock_org_where = AsyncMock()
                mock_org_where.first = AsyncMock(return_value=None)
                mock_org_select.return_value.where.return_value = mock_org_where

                with pytest.raises(ValueError, match="not found"):
                    await UserService.create_user_with_shield(
                        email="test@example.com",
                        password_hash="hash",
                        organization_id=org_id
                    )

    @pytest.mark.asyncio
    async def test_create_user_inactive_organization(self):
        """Test user creation fails with inactive organization."""
        org_id = str(uuid.uuid4())

        mock_org = MagicMock(spec=Organization)
        mock_org.id = org_id
        mock_org.is_active = False

        with patch.object(User, 'select') as mock_user_select:
            mock_where = AsyncMock()
            mock_where.first = AsyncMock(return_value=None)
            mock_user_select.return_value.where.return_value = mock_where

            with patch.object(Organization, 'select') as mock_org_select:
                mock_org_where = AsyncMock()
                mock_org_where.first = AsyncMock(return_value=mock_org)
                mock_org_select.return_value.where.return_value = mock_org_where

                with pytest.raises(ValueError, match="not active"):
                    await UserService.create_user_with_shield(
                        email="test@example.com",
                        password_hash="hash",
                        organization_id=org_id
                    )


class TestUserServiceGetUserByShieldAddress:
    """Test UserService.get_user_by_shield_address method."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_success(self):
        """Test user lookup via username field."""
        shield_address = "testuser@cellophanemail.com"

        mock_user = MagicMock(spec=User)
        mock_user.id = str(uuid.uuid4())
        mock_user.username = "testuser"
        mock_user.email = "real@example.com"
        mock_user.is_active = True

        with patch.object(User, 'select') as mock_select:
            mock_where = AsyncMock()
            mock_where.first = AsyncMock(return_value=mock_user)
            mock_select.return_value.where.return_value = mock_where

            user = await UserService.get_user_by_shield_address(shield_address)

            assert user == mock_user
            assert user.is_active is True

    @pytest.mark.asyncio
    async def test_get_user_by_uuid_extraction(self):
        """Test user lookup via UUID extraction from shield."""
        user_uuid = str(uuid.uuid4())
        shield_address = f"{user_uuid.replace('-', '')}@cellophanemail.com"

        mock_user = MagicMock(spec=User)
        mock_user.id = user_uuid
        mock_user.email = "real@example.com"
        mock_user.is_active = True

        with patch.object(User, 'select') as mock_user_select:
            # First call returns None (no username match)
            # Second call returns user (UUID match)
            mock_where_1 = AsyncMock()
            mock_where_1.first = AsyncMock(return_value=None)

            mock_where_2 = AsyncMock()
            mock_where_2.first = AsyncMock(return_value=mock_user)

            mock_user_select.return_value.where.side_effect = [mock_where_1, mock_where_2]

            with patch.object(ShieldAddress, 'get_user_id_from_shield', new_callable=AsyncMock, return_value=user_uuid):
                user = await UserService.get_user_by_shield_address(shield_address)

                assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_user_database_fallback(self):
        """Test user lookup falls back to database query."""
        shield_address = "abc123@cellophanemail.com"
        user_id = str(uuid.uuid4())

        mock_shield_record = {"user": user_id, "is_active": True}
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.is_active = True

        with patch.object(User, 'select') as mock_user_select:
            # First call: no username match
            mock_where_1 = AsyncMock()
            mock_where_1.first = AsyncMock(return_value=None)

            # Second call: user found by ID
            mock_where_2 = AsyncMock()
            mock_where_2.first = AsyncMock(return_value=mock_user)

            mock_user_select.return_value.where.side_effect = [mock_where_1, mock_where_2]

            with patch.object(ShieldAddress, 'get_user_id_from_shield', new_callable=AsyncMock, return_value=None):
                with patch.object(ShieldAddress, 'select') as mock_shield_select:
                    mock_shield_where = AsyncMock()
                    mock_shield_where.first = AsyncMock(return_value=mock_shield_record)
                    mock_shield_select.return_value.where.return_value = mock_shield_where

                    user = await UserService.get_user_by_shield_address(shield_address)

                    assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_user_filters_inactive_users(self):
        """Test lookup filters out inactive users."""
        shield_address = "test@cellophanemail.com"
        user_id = str(uuid.uuid4())

        mock_user = {"id": user_id, "is_active": False}

        with patch.object(User, 'select') as mock_user_select:
            mock_where_1 = AsyncMock()
            mock_where_1.first = AsyncMock(return_value=None)

            mock_where_2 = AsyncMock()
            mock_where_2.first = AsyncMock(return_value=mock_user)

            mock_user_select.return_value.where.side_effect = [mock_where_1, mock_where_2]

            with patch.object(ShieldAddress, 'get_user_id_from_shield', new_callable=AsyncMock, return_value=user_id):
                user = await UserService.get_user_by_shield_address(shield_address)

                assert user is None

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        """Test lookup returns None when user not found."""
        shield_address = "notfound@cellophanemail.com"

        with patch.object(User, 'select') as mock_user_select:
            mock_where = AsyncMock()
            mock_where.first = AsyncMock(return_value=None)
            mock_user_select.return_value.where.return_value = mock_where

            with patch.object(ShieldAddress, 'get_user_id_from_shield', new_callable=AsyncMock, return_value=None):
                with patch.object(ShieldAddress, 'select') as mock_shield_select:
                    mock_shield_where = AsyncMock()
                    mock_shield_where.first = AsyncMock(return_value=None)
                    mock_shield_select.return_value.where.return_value = mock_shield_where

                    user = await UserService.get_user_by_shield_address(shield_address)

                    assert user is None


class TestUserServiceDeactivateShields:
    """Test UserService.deactivate_user_shields method."""

    @pytest.mark.asyncio
    async def test_deactivate_multiple_shields(self):
        """Test deactivating multiple shield addresses."""
        user_id = str(uuid.uuid4())

        mock_shield_1 = MagicMock(spec=ShieldAddress)
        mock_shield_1.deactivate = AsyncMock()

        mock_shield_2 = MagicMock(spec=ShieldAddress)
        mock_shield_2.deactivate = AsyncMock()

        with patch.object(ShieldAddress, 'select') as mock_select:
            mock_where = AsyncMock()
            mock_where.return_value = [mock_shield_1, mock_shield_2]
            mock_select.return_value.where = mock_where

            count = await UserService.deactivate_user_shields(user_id)

            assert count == 2
            mock_shield_1.deactivate.assert_called_once()
            mock_shield_2.deactivate.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_no_shields(self):
        """Test deactivating when user has no shields."""
        user_id = str(uuid.uuid4())

        with patch.object(ShieldAddress, 'select') as mock_select:
            mock_where = AsyncMock()
            mock_where.return_value = []
            mock_select.return_value.where = mock_where

            count = await UserService.deactivate_user_shields(user_id)

            assert count == 0

    @pytest.mark.asyncio
    async def test_deactivate_shields_handles_errors(self):
        """Test error handling during shield deactivation."""
        user_id = str(uuid.uuid4())

        with patch.object(ShieldAddress, 'select') as mock_select:
            mock_select.side_effect = Exception("Database error")

            count = await UserService.deactivate_user_shields(user_id)

            assert count == 0


class TestUserServiceCreateAdditionalShield:
    """Test UserService.create_additional_shield method."""

    @pytest.mark.asyncio
    async def test_create_additional_shield_success(self):
        """Test successful creation of additional shield."""
        user_id = str(uuid.uuid4())

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.is_active = True

        with patch.object(User, 'select') as mock_user_select:
            mock_user_where = AsyncMock()
            mock_user_where.first = AsyncMock(return_value=mock_user)
            mock_user_select.return_value.where.return_value = mock_user_where

            with patch.object(ShieldAddress, 'select') as mock_shield_select:
                # No existing shield with same address
                mock_shield_where = AsyncMock()
                mock_shield_where.first = AsyncMock(return_value=None)
                mock_shield_select.return_value.where.return_value = mock_shield_where

                with patch.object(ShieldAddress, 'save', new_callable=AsyncMock):
                    shield = await UserService.create_additional_shield(user_id)

                    assert shield is not None
                    assert "@cellophanemail.com" in shield.shield_address
                    assert len(shield.shield_address.split("@")[0]) == 32  # UUID without hyphens

    @pytest.mark.asyncio
    async def test_create_additional_shield_user_not_found(self):
        """Test additional shield creation fails for non-existent user."""
        user_id = str(uuid.uuid4())

        with patch.object(User, 'select') as mock_select:
            mock_where = AsyncMock()
            mock_where.first = AsyncMock(return_value=None)
            mock_select.return_value.where.return_value = mock_where

            shield = await UserService.create_additional_shield(user_id)

            assert shield is None

    @pytest.mark.asyncio
    async def test_create_additional_shield_inactive_user(self):
        """Test additional shield creation fails for inactive user."""
        user_id = str(uuid.uuid4())

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.is_active = False

        with patch.object(User, 'select') as mock_select:
            mock_where = AsyncMock()
            mock_where.first = AsyncMock(return_value=mock_user)
            mock_select.return_value.where.return_value = mock_where

            shield = await UserService.create_additional_shield(user_id)

            assert shield is None

    @pytest.mark.asyncio
    async def test_create_additional_shield_duplicate_address(self):
        """Test additional shield creation handles duplicate addresses."""
        user_id = str(uuid.uuid4())

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.is_active = True

        mock_existing_shield = MagicMock(spec=ShieldAddress)

        with patch.object(User, 'select') as mock_user_select:
            mock_user_where = AsyncMock()
            mock_user_where.first = AsyncMock(return_value=mock_user)
            mock_user_select.return_value.where.return_value = mock_user_where

            with patch.object(ShieldAddress, 'select') as mock_shield_select:
                # Shield already exists
                mock_shield_where = AsyncMock()
                mock_shield_where.first = AsyncMock(return_value=mock_existing_shield)
                mock_shield_select.return_value.where.return_value = mock_shield_where

                shield = await UserService.create_additional_shield(user_id)

                assert shield is None


class TestShieldAddressService:
    """Test ShieldAddressService utility methods."""

    def test_generate_shield_address(self):
        """Test shield address generation from UUID."""
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        shield = ShieldAddressService.generate_shield_address(user_uuid)

        assert shield == "550e8400e29b41d4a716446655440000@cellophanemail.com"
        assert "@" in shield
        assert len(shield.split("@")[0]) == 32

    def test_generate_shield_address_custom_domain(self):
        """Test shield address generation with custom domain."""
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        shield = ShieldAddressService.generate_shield_address(user_uuid, domain="custom.com")

        assert shield == "550e8400e29b41d4a716446655440000@custom.com"

    def test_validate_shield_format_valid(self):
        """Test validation of valid shield address format."""
        shield = "550e8400e29b41d4a716446655440000@cellophanemail.com"

        is_valid = ShieldAddressService.validate_shield_format(shield)

        assert is_valid is True

    def test_validate_shield_format_invalid_domain(self):
        """Test validation fails for wrong domain."""
        shield = "550e8400e29b41d4a716446655440000@wrong.com"

        is_valid = ShieldAddressService.validate_shield_format(shield)

        assert is_valid is False

    def test_validate_shield_format_invalid_length(self):
        """Test validation fails for incorrect UUID length."""
        shield = "short@cellophanemail.com"

        is_valid = ShieldAddressService.validate_shield_format(shield)

        assert is_valid is False

    def test_validate_shield_format_invalid_hex(self):
        """Test validation fails for non-hex characters."""
        shield = "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz@cellophanemail.com"

        is_valid = ShieldAddressService.validate_shield_format(shield)

        assert is_valid is False

    def test_validate_shield_format_missing_at_symbol(self):
        """Test validation fails without @ symbol."""
        shield = "550e8400e29b41d4a716446655440000"

        is_valid = ShieldAddressService.validate_shield_format(shield)

        assert is_valid is False

    def test_validate_shield_format_custom_domain(self):
        """Test validation with custom domain."""
        shield = "550e8400e29b41d4a716446655440000@custom.com"

        is_valid = ShieldAddressService.validate_shield_format(shield, domain="custom.com")

        assert is_valid is True
