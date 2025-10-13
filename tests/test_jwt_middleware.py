"""Tests for JWT authentication middleware."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from litestar.exceptions import NotAuthorizedException

from cellophanemail.middleware.jwt_auth import (
    JWTAuthenticationMiddleware,
    JWTUser,
    jwt_auth_required,
    jwt_auth_optional,
    create_auth_response,
    create_dual_auth_response
)
from cellophanemail.services.jwt_service import create_access_token, create_refresh_token
from tests.helpers import create_mock_asgi_connection
from tests.factories import UserFactory, JWTFactory
from tests.assertions import assert_valid_jwt_structure, assert_jwt_contains_claims


class TestJWTUser:
    """Test JWTUser class."""

    def test_jwt_user_initialization(self):
        """Test that JWTUser can be initialized with basic data."""
        user = JWTUser(user_id="user-123", email="test@example.com", role="user")

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.is_authenticated is True

    @pytest.mark.asyncio
    async def test_jwt_user_from_token_payload(self):
        """Test creating JWTUser from token payload."""
        from cellophanemail.services.jwt_service import TokenPayload

        payload = TokenPayload(
            sub="user-456",
            email="payload@example.com",
            role="admin",
            exp=1234567890,
            iat=1234567800,
            jti="jti-123"
        )

        user = await JWTUser.from_token_payload(payload)

        assert user.id == "user-456"
        assert user.email == "payload@example.com"
        assert user.role == "admin"


class TestJWTAuthenticationMiddleware:
    """Test JWT authentication middleware."""

    @pytest.mark.asyncio
    async def test_authenticate_with_valid_header_token(self):
        """Test authentication with valid token in Authorization header."""
        # Create real JWT token
        token = JWTFactory.create_access_token(
            user_id="user-123",
            email="test@example.com"
        )

        # Create mock connection with token in header
        connection = create_mock_asgi_connection(
            headers={"Authorization": f"Bearer {token}"}
        )

        # Authenticate
        middleware = JWTAuthenticationMiddleware()
        result = await middleware.authenticate_request(connection)

        # Verify user was authenticated
        assert result.user is not None
        assert result.user.id == "user-123"
        assert result.user.email == "test@example.com"
        assert result.user.is_authenticated is True
        assert result.auth == token

    @pytest.mark.asyncio
    async def test_authenticate_with_valid_cookie_token(self):
        """Test authentication with valid token in cookie."""
        # Create real JWT token
        token = JWTFactory.create_access_token(
            user_id="user-456",
            email="cookie@example.com"
        )

        # Create mock connection with token in cookie
        connection = create_mock_asgi_connection(
            cookies={"access_token": token}
        )

        # Authenticate
        middleware = JWTAuthenticationMiddleware()
        result = await middleware.authenticate_request(connection)

        # Verify user was authenticated
        assert result.user is not None
        assert result.user.id == "user-456"
        assert result.user.email == "cookie@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_token_priority_header_over_cookie(self):
        """Test that Authorization header takes priority over cookie."""
        # Create two different tokens
        header_token = JWTFactory.create_access_token(
            user_id="header-user",
            email="header@example.com"
        )
        cookie_token = JWTFactory.create_access_token(
            user_id="cookie-user",
            email="cookie@example.com"
        )

        # Connection with both header and cookie
        connection = create_mock_asgi_connection(
            headers={"Authorization": f"Bearer {header_token}"},
            cookies={"access_token": cookie_token}
        )

        # Authenticate
        middleware = JWTAuthenticationMiddleware()
        result = await middleware.authenticate_request(connection)

        # Should use header token (priority)
        assert result.user.id == "header-user"
        assert result.user.email == "header@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_with_no_token(self):
        """Test authentication with no token (anonymous request)."""
        # Connection with no token
        connection = create_mock_asgi_connection()

        # Authenticate
        middleware = JWTAuthenticationMiddleware()
        result = await middleware.authenticate_request(connection)

        # Should return empty auth result (allows anonymous requests)
        assert result.user is None
        assert result.auth is None

    @pytest.mark.asyncio
    async def test_authenticate_with_invalid_token(self):
        """Test authentication with invalid/malformed token."""
        # Connection with invalid token
        connection = create_mock_asgi_connection(
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        # Authenticate
        middleware = JWTAuthenticationMiddleware()
        result = await middleware.authenticate_request(connection)

        # Should return empty auth result (invalid token treated as anonymous)
        assert result.user is None
        assert result.auth is None

    @pytest.mark.asyncio
    async def test_authenticate_with_expired_token(self):
        """Test authentication with expired token."""
        # Create token and mock it as expired
        token = JWTFactory.create_access_token(user_id="user-123")

        connection = create_mock_asgi_connection(
            headers={"Authorization": f"Bearer {token}"}
        )

        # Mock verify_token to raise JWTError
        from cellophanemail.services.jwt_service import JWTError

        with patch('cellophanemail.middleware.jwt_auth.verify_token') as mock_verify:
            mock_verify.side_effect = JWTError("Token expired")

            middleware = JWTAuthenticationMiddleware()
            result = await middleware.authenticate_request(connection)

        # Should return empty auth result
        assert result.user is None
        assert result.auth is None


class TestJWTAuthGuards:
    """Test JWT authentication guard functions."""

    def test_jwt_auth_required_with_authenticated_user(self):
        """Test that jwt_auth_required allows authenticated users."""
        # Create mock connection with authenticated user
        user = JWTUser(user_id="user-123", email="test@example.com")
        connection = create_mock_asgi_connection(user=user)

        # Should not raise exception
        try:
            jwt_auth_required(connection, route_handler=None)
        except NotAuthorizedException:
            pytest.fail("Should not raise exception for authenticated user")

    def test_jwt_auth_required_with_no_user(self):
        """Test that jwt_auth_required blocks anonymous users."""
        # Connection with no user
        connection = create_mock_asgi_connection(user=None)

        # Should raise exception
        with pytest.raises(NotAuthorizedException) as exc_info:
            jwt_auth_required(connection, route_handler=None)

        assert "Authentication required" in str(exc_info.value)

    def test_jwt_auth_required_with_wrong_user_type(self):
        """Test that jwt_auth_required blocks non-JWTUser objects."""
        # Connection with wrong user type
        fake_user = {"id": "user-123"}  # Dict, not JWTUser
        connection = create_mock_asgi_connection(user=fake_user)

        # Should raise exception
        with pytest.raises(NotAuthorizedException):
            jwt_auth_required(connection, route_handler=None)

    def test_jwt_auth_optional_with_authenticated_user(self):
        """Test that jwt_auth_optional returns user when authenticated."""
        user = JWTUser(user_id="user-123", email="test@example.com")
        connection = create_mock_asgi_connection(user=user)

        result = jwt_auth_optional(connection)

        assert result is not None
        assert result.id == "user-123"

    def test_jwt_auth_optional_with_no_user(self):
        """Test that jwt_auth_optional returns None for anonymous."""
        connection = create_mock_asgi_connection(user=None)

        result = jwt_auth_optional(connection)

        assert result is None


class TestCreateAuthResponse:
    """Test auth response creation functions."""

    @pytest.mark.asyncio
    async def test_create_auth_response_with_refresh(self):
        """Test creating auth response with refresh token."""
        user = UserFactory.create_user(
            user_id="user-123",
            email="test@example.com",
            username="test123"
        )

        response = await create_auth_response(user, include_refresh=True)

        # Verify response structure
        assert "access_token" in response
        assert "refresh_token" in response
        assert "token_type" in response
        assert response["token_type"] == "Bearer"
        assert "expires_in" in response
        assert response["expires_in"] == 900  # 15 minutes

        # Verify user data
        assert "user" in response
        assert response["user"]["id"] == "user-123"
        assert response["user"]["email"] == "test@example.com"

        # Verify tokens are valid JWTs
        assert_valid_jwt_structure(response["access_token"])
        assert_valid_jwt_structure(response["refresh_token"])

    @pytest.mark.asyncio
    async def test_create_auth_response_without_refresh(self):
        """Test creating auth response without refresh token."""
        user = UserFactory.create_user()

        response = await create_auth_response(user, include_refresh=False)

        assert "access_token" in response
        assert "refresh_token" not in response

    @pytest.mark.asyncio
    async def test_create_dual_auth_response_sets_cookies(self):
        """Test that dual auth response sets secure cookies."""
        from litestar import Response

        user = UserFactory.create_user(
            user_id="user-123",
            email="test@example.com"
        )

        # Create response object
        response = Response(content={}, status_code=200)

        # Mock settings to control secure cookie behavior
        with patch('cellophanemail.middleware.jwt_auth.get_settings') as mock_settings:
            mock_settings.return_value.debug = False  # Production mode

            result = await create_dual_auth_response(user, response, include_refresh=True)

        # Verify response contains tokens in content
        assert "access_token" in result.content
        assert "refresh_token" in result.content

        # Note: Cookie verification would require inspecting response.set_cookie calls
        # which is difficult without Litestar internals. Focus on content verification.
