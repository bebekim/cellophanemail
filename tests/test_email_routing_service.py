"""Tests for email routing service."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from cellophanemail.services.email_routing_service import (
    EmailRoutingService,
    EmailRoutingContext
)
from tests.factories import UserFactory
from tests.assertions import assert_valid_email_routing_context


class TestEmailRoutingService:
    """Test EmailRoutingService core functionality."""

    def test_service_initialization(self):
        """Test service can be initialized with custom domain."""
        service = EmailRoutingService(valid_domain="custom.com")

        assert service.valid_domain == "custom.com"

    def test_service_default_domain(self):
        """Test service uses default domain."""
        service = EmailRoutingService()

        assert service.valid_domain == "cellophanemail.com"


class TestDomainValidation:
    """Test _validate_domain method."""

    def test_valid_domain(self):
        """Test shield address with valid domain."""
        service = EmailRoutingService(valid_domain="cellophanemail.com")
        context = EmailRoutingContext(shield_address="test@cellophanemail.com")

        result = service._validate_domain(context)

        assert result is True
        assert context.is_valid_domain is True
        assert context.error_code is None

    def test_invalid_domain(self):
        """Test shield address with wrong domain."""
        service = EmailRoutingService(valid_domain="cellophanemail.com")
        context = EmailRoutingContext(shield_address="test@wrongdomain.com")

        result = service._validate_domain(context)

        assert result is False
        assert context.is_valid_domain is False
        assert context.error_code == "INVALID_DOMAIN"
        assert "Invalid domain" in context.error_message

    def test_case_insensitive_domain(self):
        """Test domain validation is case-insensitive."""
        service = EmailRoutingService(valid_domain="cellophanemail.com")
        context = EmailRoutingContext(shield_address="test@CELLOPHANEMAIL.COM")

        result = service._validate_domain(context)

        assert result is True


class TestUserLookup:
    """Test _lookup_user method."""

    @pytest.mark.asyncio
    async def test_lookup_existing_user_dict_response(self):
        """Test lookup returns user data as dictionary."""
        service = EmailRoutingService()
        context = EmailRoutingContext(shield_address="test123@cellophanemail.com")

        # Mock UserService returning dict
        user_dict = UserFactory.create_user_dict(
            user_id="user-123",
            email="real@example.com",
            username="test123"
        )

        with patch('cellophanemail.services.email_routing_service.UserService') as MockUserService:
            MockUserService.get_user_by_shield_address = AsyncMock(return_value=user_dict)

            result = await service._lookup_user(context)

        assert result is True
        assert context.user_id == "user-123"
        assert context.user_email == "real@example.com"
        assert context.error_code is None

    @pytest.mark.asyncio
    async def test_lookup_existing_user_object_response(self):
        """Test lookup returns user data as model object."""
        service = EmailRoutingService()
        context = EmailRoutingContext(shield_address="test456@cellophanemail.com")

        # Mock UserService returning User object
        user_obj = UserFactory.create_user(
            user_id="user-456",
            email="object@example.com"
        )

        with patch('cellophanemail.services.email_routing_service.UserService') as MockUserService:
            MockUserService.get_user_by_shield_address = AsyncMock(return_value=user_obj)

            result = await service._lookup_user(context)

        assert result is True
        assert context.user_id == "user-456"
        assert context.user_email == "object@example.com"

    @pytest.mark.asyncio
    async def test_lookup_nonexistent_user(self):
        """Test lookup with shield address not in database."""
        service = EmailRoutingService()
        context = EmailRoutingContext(shield_address="notfound@cellophanemail.com")

        with patch('cellophanemail.services.email_routing_service.UserService') as MockUserService:
            MockUserService.get_user_by_shield_address = AsyncMock(return_value=None)

            result = await service._lookup_user(context)

        assert result is False
        assert context.user_id is None
        assert context.error_code == "USER_NOT_FOUND"
        assert "not found" in context.error_message.lower()

    @pytest.mark.asyncio
    async def test_lookup_database_error(self):
        """Test lookup handles database errors gracefully."""
        service = EmailRoutingService()
        context = EmailRoutingContext(shield_address="error@cellophanemail.com")

        with patch('cellophanemail.services.email_routing_service.UserService') as MockUserService:
            MockUserService.get_user_by_shield_address = AsyncMock(
                side_effect=Exception("Database connection error")
            )

            result = await service._lookup_user(context)

        assert result is False
        assert context.error_code == "LOOKUP_ERROR"


class TestUserStatusVerification:
    """Test _verify_user_active method."""

    def test_verify_complete_user_info(self):
        """Test verification with complete user information."""
        service = EmailRoutingService()
        context = EmailRoutingContext(
            shield_address="test@cellophanemail.com",
            user_id="user-123",
            user_email="real@example.com"
        )

        result = service._verify_user_active(context)

        assert result is True
        assert context.error_code is None

    def test_verify_missing_user_id(self):
        """Test verification fails without user_id."""
        service = EmailRoutingService()
        context = EmailRoutingContext(
            shield_address="test@cellophanemail.com",
            user_id=None,
            user_email="real@example.com"
        )

        result = service._verify_user_active(context)

        assert result is False
        assert context.error_code == "USER_INCOMPLETE"

    def test_verify_missing_user_email(self):
        """Test verification fails without user_email."""
        service = EmailRoutingService()
        context = EmailRoutingContext(
            shield_address="test@cellophanemail.com",
            user_id="user-123",
            user_email=None
        )

        result = service._verify_user_active(context)

        assert result is False
        assert context.error_code == "USER_INCOMPLETE"


class TestValidateAndRouteEmail:
    """Test validate_and_route_email orchestration method."""

    @pytest.mark.asyncio
    async def test_successful_routing(self):
        """Test complete successful routing flow."""
        service = EmailRoutingService(valid_domain="cellophanemail.com")

        # Mock user lookup
        user_dict = UserFactory.create_user_dict(
            user_id="user-success",
            email="success@example.com"
        )

        with patch('cellophanemail.services.email_routing_service.UserService') as MockUserService:
            MockUserService.get_user_by_shield_address = AsyncMock(return_value=user_dict)

            context = await service.validate_and_route_email("shield@cellophanemail.com")

        # Verify successful routing
        assert_valid_email_routing_context(context, should_be_valid=True)
        assert context.is_active_user is True
        assert context.user_id == "user-success"

    @pytest.mark.asyncio
    async def test_routing_fails_on_invalid_domain(self):
        """Test routing stops at domain validation."""
        service = EmailRoutingService(valid_domain="cellophanemail.com")

        context = await service.validate_and_route_email("shield@wrongdomain.com")

        assert_valid_email_routing_context(context, should_be_valid=False)
        assert context.error_code == "INVALID_DOMAIN"
        assert context.is_valid_domain is False

    @pytest.mark.asyncio
    async def test_routing_fails_on_user_not_found(self):
        """Test routing stops at user lookup."""
        service = EmailRoutingService()

        with patch('cellophanemail.services.email_routing_service.UserService') as MockUserService:
            MockUserService.get_user_by_shield_address = AsyncMock(return_value=None)

            context = await service.validate_and_route_email("notfound@cellophanemail.com")

        assert_valid_email_routing_context(context, should_be_valid=False)
        assert context.error_code == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_routing_normalizes_shield_address(self):
        """Test routing normalizes shield address (lowercase, trim)."""
        service = EmailRoutingService()

        user_dict = UserFactory.create_user_dict()
        with patch('cellophanemail.services.email_routing_service.UserService') as MockUserService:
            MockUserService.get_user_by_shield_address = AsyncMock(return_value=user_dict)

            context = await service.validate_and_route_email("  SHIELD@CELLOPHANEMAIL.COM  ")

        assert context.shield_address == "shield@cellophanemail.com"


class TestHTTPStatusMapping:
    """Test get_http_status_code method."""

    def test_status_code_for_success(self):
        """Test status code for successful routing."""
        service = EmailRoutingService()
        context = EmailRoutingContext(
            shield_address="test@cellophanemail.com",
            is_active_user=True
        )

        status = service.get_http_status_code(context)

        assert status == 200

    def test_status_code_for_invalid_domain(self):
        """Test status code for invalid domain error."""
        service = EmailRoutingService()
        context = EmailRoutingContext(
            shield_address="test@wrong.com",
            error_code="INVALID_DOMAIN"
        )

        status = service.get_http_status_code(context)

        assert status == 400

    def test_status_code_for_user_not_found(self):
        """Test status code for user not found error."""
        service = EmailRoutingService()
        context = EmailRoutingContext(
            shield_address="test@cellophanemail.com",
            error_code="USER_NOT_FOUND"
        )

        status = service.get_http_status_code(context)

        assert status == 404

    def test_status_code_for_internal_error(self):
        """Test status code for internal errors."""
        service = EmailRoutingService()
        context = EmailRoutingContext(
            shield_address="test@cellophanemail.com",
            error_code="ROUTING_ERROR"
        )

        status = service.get_http_status_code(context)

        assert status == 500


class TestErrorResponseFormatting:
    """Test format_error_response method."""

    def test_format_error_response(self):
        """Test error response formatting."""
        service = EmailRoutingService()
        context = EmailRoutingContext(
            shield_address="error@cellophanemail.com",
            error_code="USER_NOT_FOUND",
            error_message="Shield address not found"
        )

        response = service.format_error_response(context, message_id="msg-123")

        assert response["error"] == "Shield address not found"
        assert response["error_code"] == "USER_NOT_FOUND"
        assert response["message_id"] == "msg-123"
        assert response["shield_address"] == "error@cellophanemail.com"
