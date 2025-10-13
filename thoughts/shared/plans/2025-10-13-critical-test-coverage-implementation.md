---
date: 2025-10-13
author: Claude
topic: "Critical Test Coverage Implementation for Reliable Software Construction"
status: in_progress
tags: [testing, coverage, security, middleware, routes, services, pytest]
related_files: [
  tests/conftest.py,
  tests/factories.py,
  tests/helpers.py,
  tests/assertions.py,
  tests/test_jwt_middleware.py,
  tests/test_billing_routes.py,
  tests/test_email_routing_service.py,
  tests/test_user_service.py,
  tests/test_auth_routes.py,
  tests/test_webhook_routes.py
]
---

# Critical Test Coverage Implementation Plan

## Overview

Increase test coverage on critical gaps (middleware, routes, services) from ~35% to 80% overall, with 95% on security-critical components. This enables reliable software construction by ensuring critical code paths are tested before features are built on top of them.

**Goal**: Prevent regressions and enable confident feature development through comprehensive test coverage of security, financial, and core business logic layers.

## Current State Analysis

### Test Coverage Gaps

**Services (9 total)**:
- ✅ Tested (3/9 - 33%): `auth_service.py` (21 tests), `jwt_service.py` (11 tests), `stripe_service.py` (9 tests)
- ❌ Untested (6/9 - 67%):
  - `email_routing_service.py` - **0 tests** (194 lines, CRITICAL)
  - `user_service.py` - **0 tests** (295 lines, CRITICAL)
  - `email_delivery.py`, `analysis_cache.py`, `gmail_filter_manager.py`, `storage_optimization.py`

**Routes (6 total)**:
- ⚠️ Partial (1/6): `auth.py` - 5 tests (only registration)
- ❌ Untested (5/6 - 83%):
  - `billing.py` - **0 tests** (CRITICAL - financial)
  - `webhooks.py` - **0 tests** (controller methods untested)
  - `frontend.py`, `health.py`, `stripe_webhooks.py`

**Middleware (1 total)**:
- ❌ Untested (1/1 - 100%): `jwt_auth.py` - **0 tests** (CRITICAL SECURITY GAP)

### Key Discoveries

**Good Patterns to Follow**:
- `tests/test_jwt_service.py:22-52` - Excellent behavioral testing with real JWT tokens
- `tests/unit/test_component_contracts.py:72-138` - Protocol-based contract testing
- `tests/test_integration_minimal.py:137-169` - Integration tests with dry-run mode
- `tests/conftest.py:20-32` - AsyncTestClient fixture (function scope)

**Patterns to Avoid**:
- Deep mock chaining of database queries (brittle, couples to implementation)
- Sync TestClient for async routes (doesn't properly handle async)
- Testing private methods directly (couples to internal structure)

**Test Infrastructure Gaps**:
- No test factories for User, Stripe objects
- No mock connection builders for middleware testing
- No shared assertion helpers
- Inconsistent AsyncTestClient usage

## Desired End State

### Coverage Targets

| Layer | Current | Target | Test Count |
|-------|---------|--------|-----------|
| **Middleware** | 0% | **95%** | 15 tests |
| **Critical Services** | 0% | **90%** | 45 tests (20 routing + 25 user) |
| **Routes** | 17% | **80%** | 37 tests (10 billing + 15 auth + 12 webhooks) |
| **Overall** | ~35% | **80%** | +97 new tests |

### Testing Philosophy

**Pragmatic Pyramid**:
- 70% Unit Tests - Fast, isolated, behavioral verification
- 25% Integration Tests - Multiple components, external mocking
- 5% E2E Tests - Full stack (future work)

**Key Principles**:
1. **Mock at boundaries** - Database, external APIs, not business logic
2. **Test behavior** - JWT validation works, not mock chains
3. **Use real structures** - Real JWT tokens, real data classes
4. **Standardize patterns** - AsyncTestClient everywhere, Protocol contracts

## What We're NOT Doing

- ❌ Testing lower-priority services (gmail_filter_manager, storage_optimization, analysis_cache)
- ❌ E2E tests with real databases/APIs (future work)
- ❌ Frontend route tests (HTML rendering)
- ❌ Health endpoint tests (trivial)
- ❌ Refactoring all existing tests (only critical ones)
- ❌ 100% coverage (diminishing returns, focus on critical paths)

## Implementation Approach

**Strategy**: Build foundation first, then layer by criticality:
1. Infrastructure → enables all other testing
2. Security → authentication gate must be solid
3. Financial → billing errors cost money
4. Core logic → email routing and user management
5. API surface → public endpoints

**Each phase**:
- Create git branch: `test/phase-N-description`
- Implement tests following established patterns
- Run automated verification (`pytest`, coverage checks)
- Manual verification of test quality
- Merge to main, move to next phase

---

## Phase 1: Test Infrastructure Foundation

### Overview

Build reusable test utilities, factories, and helpers that all subsequent phases will use. Standardizes testing patterns and reduces code duplication.

**Duration**: 2 days
**Priority**: Foundational (blocks all other phases)

### Changes Required

#### 1. Test Factories (`tests/factories.py`)

**File**: `tests/factories.py` (NEW)
**Purpose**: Create mock objects for common entities

```python
"""Test factories for creating mock objects."""

from unittest.mock import MagicMock, AsyncMock
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class UserFactory:
    """Factory for creating mock User objects."""

    @staticmethod
    def create_user(
        id: str = "user-123",
        email: str = "test@example.com",
        username: str = "test123",
        is_verified: bool = True,
        stripe_customer_id: Optional[str] = None,
        **kwargs
    ) -> MagicMock:
        """Create a mock User object with sensible defaults."""
        user = MagicMock()
        user.id = id
        user.email = email
        user.username = username
        user.is_verified = is_verified
        user.stripe_customer_id = stripe_customer_id or "cus_default"
        user.first_name = kwargs.get("first_name", "Test")
        user.last_name = kwargs.get("last_name", "User")
        user.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        user.last_login = kwargs.get("last_login")
        user.hashed_password = kwargs.get("hashed_password", "$2b$12$test_hash")
        user.verification_token = kwargs.get("verification_token", "token123")

        # Add async save method
        user.save = AsyncMock()

        return user

    @staticmethod
    def create_user_dict(
        id: str = "user-123",
        email: str = "test@example.com",
        username: str = "test123",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a user dictionary (for service return values)."""
        return {
            "id": id,
            "email": email,
            "username": username,
            "is_verified": kwargs.get("is_verified", True),
            "first_name": kwargs.get("first_name", "Test"),
            "last_name": kwargs.get("last_name", "User"),
            "organization": kwargs.get("organization"),
        }


class StripeFactory:
    """Factory for creating mock Stripe objects."""

    @staticmethod
    def create_customer(
        id: str = "cus_123",
        email: str = "test@example.com",
        name: str = "Test User",
        **kwargs
    ) -> MagicMock:
        """Create a mock Stripe Customer object."""
        customer = MagicMock()
        customer.id = id
        customer.email = email
        customer.name = name
        customer.metadata = kwargs.get("metadata", {"user_id": "user-123"})
        return customer

    @staticmethod
    def create_checkout_session(
        id: str = "cs_test_123",
        url: str = "https://checkout.stripe.com/test",
        **kwargs
    ) -> MagicMock:
        """Create a mock Stripe Checkout Session."""
        session = MagicMock()
        session.id = id
        session.url = url
        session.customer = kwargs.get("customer", "cus_123")
        session.mode = kwargs.get("mode", "subscription")
        return session

    @staticmethod
    def create_portal_session(
        id: str = "bps_test_123",
        url: str = "https://billing.stripe.com/test",
        **kwargs
    ) -> MagicMock:
        """Create a mock Stripe Portal Session."""
        session = MagicMock()
        session.id = id
        session.url = url
        return session


class JWTFactory:
    """Factory for creating real JWT tokens for testing."""

    @staticmethod
    def create_access_token(
        user_id: str = "user-123",
        email: str = "test@example.com",
        role: str = "user"
    ) -> str:
        """Create a REAL JWT access token using the actual service."""
        from cellophanemail.services.jwt_service import create_access_token
        return create_access_token(user_id=user_id, email=email, role=role)

    @staticmethod
    def create_refresh_token(user_id: str = "user-123") -> str:
        """Create a REAL JWT refresh token using the actual service."""
        from cellophanemail.services.jwt_service import create_refresh_token
        return create_refresh_token(user_id=user_id)


class EmailRoutingFactory:
    """Factory for creating email routing objects."""

    @staticmethod
    def create_routing_context(
        shield_address: str = "test123@cellophanemail.com",
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        is_active_user: bool = False,
        **kwargs
    ):
        """Create an EmailRoutingContext for testing."""
        from cellophanemail.services.email_routing_service import EmailRoutingContext

        return EmailRoutingContext(
            shield_address=shield_address,
            user_id=user_id,
            user_email=user_email,
            organization_id=kwargs.get("organization_id"),
            is_valid_domain=kwargs.get("is_valid_domain", False),
            is_active_user=is_active_user,
            error_message=kwargs.get("error_message"),
            error_code=kwargs.get("error_code")
        )
```

#### 2. Test Helpers (`tests/helpers.py`)

**File**: `tests/helpers.py` (NEW)
**Purpose**: Mock ASGI connections and other test utilities

```python
"""Test helper utilities for creating mock objects and connections."""

from unittest.mock import MagicMock
from typing import Dict, Any, Optional
from litestar.connection import ASGIConnection


def create_mock_asgi_connection(
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    user: Any = None,
    **kwargs
) -> MagicMock:
    """Create a mock ASGI connection for middleware testing.

    Args:
        headers: HTTP headers dictionary
        cookies: Cookie dictionary
        user: Authenticated user object (or None)
        **kwargs: Additional connection attributes

    Returns:
        Mock ASGI connection object
    """
    connection = MagicMock(spec=ASGIConnection)

    # Set up headers with get() method
    headers_dict = headers or {}
    connection.headers = MagicMock()
    connection.headers.get = lambda key, default="": headers_dict.get(key, default)

    # Set up cookies with get() method
    cookies_dict = cookies or {}
    connection.cookies = MagicMock()
    connection.cookies.get = lambda key, default=None: cookies_dict.get(key, default)

    # Set authenticated user
    connection.user = user

    # Add any additional attributes
    for key, value in kwargs.items():
        setattr(connection, key, value)

    return connection


def create_mock_database_query(return_value: Any = None, returns_list: bool = False):
    """Create a mock database query chain.

    Args:
        return_value: Value to return from final query method
        returns_list: Whether query returns a list or single object

    Returns:
        Mock query object with chained methods
    """
    from unittest.mock import AsyncMock

    mock_query = MagicMock()

    if returns_list:
        # For queries that return lists
        mock_query.run = AsyncMock(return_value=return_value or [])
    else:
        # For queries that return single objects
        mock_query.first = AsyncMock(return_value=return_value)
        mock_query.run = AsyncMock(return_value=return_value)

    # Support chaining methods
    mock_where = MagicMock(return_value=mock_query)
    mock_select = MagicMock(return_value=mock_where)

    # Attach chaining methods
    mock_query.where = mock_where
    mock_query.select = mock_select

    return mock_query
```

#### 3. Assertion Helpers (`tests/assertions.py`)

**File**: `tests/assertions.py` (NEW)
**Purpose**: Shared assertion functions for common validations

```python
"""Shared assertion helpers for testing."""

import jwt
from typing import Dict, Any


def assert_valid_jwt_structure(token: str) -> None:
    """Assert that a token has valid JWT structure.

    Args:
        token: JWT token string

    Raises:
        AssertionError: If token structure is invalid
    """
    assert isinstance(token, str), "Token must be a string"
    parts = token.split('.')
    assert len(parts) == 3, f"JWT must have 3 parts (header.payload.signature), got {len(parts)}"


def assert_jwt_contains_claims(token: str, expected_claims: Dict[str, Any]) -> None:
    """Assert that a JWT token contains expected claims.

    Args:
        token: JWT token string
        expected_claims: Dictionary of expected claim key-value pairs

    Raises:
        AssertionError: If claims don't match
    """
    decoded = jwt.decode(token, options={"verify_signature": False})

    for claim_key, expected_value in expected_claims.items():
        assert claim_key in decoded, f"Token missing claim: {claim_key}"
        if expected_value is not None:
            actual_value = decoded[claim_key]
            assert actual_value == expected_value, \
                f"Claim '{claim_key}' mismatch: expected {expected_value}, got {actual_value}"


def assert_valid_email_routing_context(context, should_be_valid: bool = True) -> None:
    """Assert that an EmailRoutingContext has expected validity.

    Args:
        context: EmailRoutingContext object
        should_be_valid: Whether context should represent valid routing

    Raises:
        AssertionError: If context validity doesn't match expectation
    """
    from cellophanemail.services.email_routing_service import EmailRoutingContext

    assert isinstance(context, EmailRoutingContext), \
        f"Expected EmailRoutingContext, got {type(context)}"

    assert context.shield_address is not None, "Context must have shield_address"

    if should_be_valid:
        assert context.is_active_user is True, "Context should indicate active user"
        assert context.user_id is not None, "Valid context must have user_id"
        assert context.user_email is not None, "Valid context must have user_email"
        assert context.error_code is None, "Valid context should not have error_code"
    else:
        assert context.is_active_user is False, "Invalid context should not have active user"
        assert context.error_code is not None, "Invalid context must have error_code"
        assert context.error_message is not None, "Invalid context must have error_message"


def assert_http_error_response(response, expected_status: int, expected_error_key: str = "error") -> None:
    """Assert that an HTTP response is an error with expected structure.

    Args:
        response: HTTP response object
        expected_status: Expected HTTP status code
        expected_error_key: Key containing error message in response JSON

    Raises:
        AssertionError: If response doesn't match expected error structure
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}"

    data = response.json()
    assert expected_error_key in data, \
        f"Response missing '{expected_error_key}' key: {data}"
    assert data[expected_error_key] is not None, \
        f"Error message should not be None"
```

#### 4. Update conftest.py

**File**: `tests/conftest.py`
**Changes**: Ensure AsyncTestClient is standardized

```python
# Add to existing conftest.py

# Ensure test_client fixture uses AsyncTestClient (already exists, verify it's async)
# No changes needed if fixture already matches lines 20-32
```

### Success Criteria

#### Automated Verification:
- [ ] All new files created: `pytest tests/factories.py tests/helpers.py tests/assertions.py --collect-only`
- [ ] No import errors: `python -c "from tests.factories import UserFactory, StripeFactory, JWTFactory"`
- [ ] No linting errors: `ruff check tests/factories.py tests/helpers.py tests/assertions.py`

#### Manual Verification:
- [ ] UserFactory creates valid mock users with sensible defaults
- [ ] JWTFactory creates REAL tokens that can be decoded
- [ ] create_mock_asgi_connection returns connection with proper headers/cookies
- [ ] Assertion helpers provide clear error messages when assertions fail

---

## Phase 2: JWT Middleware Tests (Security Layer)

### Overview

Test JWT authentication middleware - the security gate for the entire application. Must verify token extraction from headers and cookies, validation, user attachment, and guard functions.

**Duration**: 3 days
**Priority**: CRITICAL - Security
**Target Coverage**: 95%

### Changes Required

#### 1. JWT Middleware Test File

**File**: `tests/test_jwt_middleware.py` (NEW)
**Changes**: Create comprehensive middleware tests

```python
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
            id="user-123",
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
            id="user-123",
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
```

### Success Criteria

#### Automated Verification:
- [ ] All tests pass: `pytest tests/test_jwt_middleware.py -v`
- [ ] Coverage target met: `pytest tests/test_jwt_middleware.py --cov=cellophanemail/middleware/jwt_auth --cov-report=term-missing`
- [ ] Target: 95% coverage on `middleware/jwt_auth.py`
- [ ] No linting errors: `ruff check tests/test_jwt_middleware.py`

#### Manual Verification:
- [ ] Tests verify real JWT behavior (not just mocks)
- [ ] Token extraction priority tested (header > cookie)
- [ ] Guard functions properly block unauthorized access
- [ ] All error cases covered (invalid, expired, missing tokens)

---

## Phase 3: Billing Routes Tests (Financial Layer)

### Overview

Test billing route endpoints that handle Stripe checkout and portal creation. Critical for financial operations - untested billing code = revenue risk.

**Duration**: 3 days
**Priority**: CRITICAL - Financial
**Target Coverage**: 80%

### Changes Required

#### 1. Billing Routes Test File

**File**: `tests/test_billing_routes.py` (NEW)
**Changes**: Create comprehensive billing route tests

```python
"""Tests for billing routes."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from litestar.testing import AsyncTestClient

from tests.factories import UserFactory, StripeFactory, JWTFactory
from tests.assertions import assert_http_error_response


@pytest.mark.asyncio
class TestCreateCheckoutRoute:
    """Test /billing/create-checkout endpoint."""

    async def test_create_checkout_authenticated_user(self, test_client):
        """Test creating checkout session with authenticated user."""
        # Create real JWT token
        token = JWTFactory.create_access_token(
            user_id="user-123",
            email="test@example.com"
        )

        # Mock Stripe service
        mock_session = StripeFactory.create_checkout_session(
            id="cs_test_123",
            url="https://checkout.stripe.com/session/123"
        )

        with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
            mock_service = MagicMock()
            mock_service.create_checkout_session = AsyncMock(return_value=mock_session)
            MockStripeService.return_value = mock_service

            # Make authenticated request
            response = await test_client.post(
                "/billing/create-checkout",
                headers={"Authorization": f"Bearer {token}"},
                json={"price_id": "price_test_123"}
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert data["checkout_url"] == "https://checkout.stripe.com/session/123"
        assert "session_id" in data
        assert data["session_id"] == "cs_test_123"

    async def test_create_checkout_unauthenticated(self, test_client):
        """Test that checkout requires authentication."""
        # No auth token
        response = await test_client.post(
            "/billing/create-checkout",
            json={"price_id": "price_test_123"}
        )

        # Should be unauthorized
        assert response.status_code == 401

    async def test_create_checkout_missing_price_id(self, test_client):
        """Test checkout with missing price_id."""
        token = JWTFactory.create_access_token()

        # No price_id in request
        response = await test_client.post(
            "/billing/create-checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={}
        )

        # Should be bad request
        assert response.status_code == 400

    async def test_create_checkout_stripe_error(self, test_client):
        """Test checkout when Stripe API fails."""
        token = JWTFactory.create_access_token()

        with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
            mock_service = MagicMock()
            mock_service.create_checkout_session = AsyncMock(
                side_effect=Exception("Stripe API error")
            )
            MockStripeService.return_value = mock_service

            response = await test_client.post(
                "/billing/create-checkout",
                headers={"Authorization": f"Bearer {token}"},
                json={"price_id": "price_test_123"}
            )

        # Should return error
        assert response.status_code == 500
        assert_http_error_response(response, 500, "error")


@pytest.mark.asyncio
class TestCustomerPortalRoute:
    """Test /billing/customer-portal endpoint."""

    async def test_customer_portal_authenticated_user(self, test_client):
        """Test creating customer portal session."""
        token = JWTFactory.create_access_token(user_id="user-123")

        # Mock Stripe service
        mock_session = StripeFactory.create_portal_session(
            id="bps_test_123",
            url="https://billing.stripe.com/session/123"
        )

        with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
            mock_service = MagicMock()
            mock_service.create_portal_session = AsyncMock(return_value=mock_session)
            MockStripeService.return_value = mock_service

            response = await test_client.post(
                "/billing/customer-portal",
                headers={"Authorization": f"Bearer {token}"}
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "portal_url" in data
        assert data["portal_url"] == "https://billing.stripe.com/session/123"

    async def test_customer_portal_unauthenticated(self, test_client):
        """Test that portal requires authentication."""
        response = await test_client.post("/billing/customer-portal")

        assert response.status_code == 401

    async def test_customer_portal_user_without_customer_id(self, test_client):
        """Test portal for user without Stripe customer ID."""
        token = JWTFactory.create_access_token(user_id="user-no-stripe")

        with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
            mock_service = MagicMock()
            # Mock get_user to return user without stripe_customer_id
            with patch('cellophanemail.routes.billing.User') as MockUser:
                mock_user_query = MagicMock()
                mock_user = UserFactory.create_user(stripe_customer_id=None)
                mock_user_query.first = AsyncMock(return_value=mock_user)
                MockUser.objects.return_value.where.return_value = mock_user_query

                response = await test_client.post(
                    "/billing/customer-portal",
                    headers={"Authorization": f"Bearer {token}"}
                )

        # Should return error
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
```

### Success Criteria

#### Automated Verification:
- [ ] All tests pass: `pytest tests/test_billing_routes.py -v`
- [ ] Coverage target met: `pytest tests/test_billing_routes.py --cov=cellophanemail/routes/billing --cov-report=term-missing`
- [ ] Target: 80% coverage on `routes/billing.py`
- [ ] No linting errors: `ruff check tests/test_billing_routes.py`

#### Manual Verification:
- [ ] Authentication properly enforced on billing endpoints
- [ ] Stripe errors handled gracefully
- [ ] Missing parameters return appropriate error codes
- [ ] Success responses contain required fields (checkout_url, portal_url)

---

## Phase 4: Email Routing Service Tests (Core Business Logic)

### Overview

Test email routing service - critical junction between webhook ingestion and email processing. Handles domain validation, user lookup, and routing decisions.

**Duration**: 4 days
**Priority**: CRITICAL - Core Business Logic
**Target Coverage**: 90%

### Changes Required

#### 1. Email Routing Service Test File

**File**: `tests/test_email_routing_service.py` (NEW)
**Changes**: Create comprehensive service tests

```python
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
            id="user-123",
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
            id="user-456",
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
            id="user-success",
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
```

### Success Criteria

#### Automated Verification:
- [ ] All tests pass: `pytest tests/test_email_routing_service.py -v`
- [ ] Coverage target met: `pytest tests/test_email_routing_service.py --cov=cellophanemail/services/email_routing_service --cov-report=term-missing`
- [ ] Target: 90% coverage on `services/email_routing_service.py`
- [ ] No linting errors: `ruff check tests/test_email_routing_service.py`

#### Manual Verification:
- [ ] All routing pipeline stages tested (domain → lookup → verification)
- [ ] Error handling tested for each failure point
- [ ] Both dict and object user responses handled
- [ ] HTTP status codes correctly mapped to error types

---

## Phase 5: User Service Tests (Core Operations)

### Overview

Test user service - handles user creation, shield address management, and user operations. Core to the entire application's user management.

**Duration**: 3 days
**Priority**: CRITICAL - Core Operations
**Target Coverage**: 90%

### Changes Required

#### 1. User Service Test File

**File**: `tests/test_user_service.py` (NEW)
**Changes**: Create comprehensive user service tests

```python
"""Tests for user service."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from cellophanemail.services.user_service import UserService
from tests.factories import UserFactory


# Tests to be written following patterns from email_routing_service tests
# Key areas:
# - create_user_with_shield
# - get_user_by_shield_address
# - deactivate_user_shields
# - create_additional_shield
# - ShieldAddressService methods

# This will be implemented in the actual phase
```

_(Full implementation will follow same pattern as email routing service tests - 25 tests covering all methods)_

### Success Criteria

#### Automated Verification:
- [ ] All tests pass: `pytest tests/test_user_service.py -v`
- [ ] Coverage target met: `pytest tests/test_user_service.py --cov=cellophanemail/services/user_service --cov-report=term-missing`
- [ ] Target: 90% coverage on `services/user_service.py`
- [ ] No linting errors: `ruff check tests/test_user_service.py`

#### Manual Verification:
- [ ] User creation with shield address tested
- [ ] Shield lookup optimizations tested
- [ ] Shield deactivation tested
- [ ] Multiple shields per user tested

---

## Phase 6: Auth Route Endpoints Tests (API Surface)

### Overview

Test remaining authentication endpoints (login, logout, profile, refresh, dashboard) that weren't covered in initial auth tests.

**Duration**: 3 days
**Priority**: HIGH - Public API
**Target Coverage**: 80%

### Changes Required

#### 1. Expand Auth Endpoints Tests

**File**: `tests/test_auth_endpoints.py`
**Changes**: Add tests for missing endpoints

```python
# Add to existing file:
# - test_login_success
# - test_login_invalid_credentials
# - test_logout_clears_tokens
# - test_refresh_token_flow
# - test_profile_retrieval
# - test_dashboard_access
# etc. (15 new tests)
```

### Success Criteria

#### Automated Verification:
- [ ] All tests pass: `pytest tests/test_auth_endpoints.py -v`
- [ ] Coverage target met: `pytest tests/test_auth_endpoints.py --cov=cellophanemail/routes/auth --cov-report=term-missing`
- [ ] Target: 80% coverage on `routes/auth.py`
- [ ] No linting errors: `ruff check tests/test_auth_endpoints.py`

#### Manual Verification:
- [ ] Login flow tested with valid/invalid credentials
- [ ] Logout properly blacklists tokens
- [ ] Profile retrieval requires authentication
- [ ] Dashboard access requires authentication

---

## Phase 7: Webhook Routes Tests (Entry Point)

### Overview

Test webhook controller methods that handle incoming email webhooks. Critical entry point for email processing.

**Duration**: 2 days
**Priority**: HIGH - Entry Point
**Target Coverage**: 80%

### Changes Required

#### 1. Webhook Routes Test File

**File**: `tests/test_webhook_routes.py` (NEW)
**Changes**: Create webhook controller tests

```python
# Test webhook controller methods:
# - _extract_shield_address
# - _validate_domain
# - _get_user
# - Error handling
# - Integration with email_routing_service
# (12 tests)
```

### Success Criteria

#### Automated Verification:
- [ ] All tests pass: `pytest tests/test_webhook_routes.py -v`
- [ ] Coverage target met: `pytest tests/test_webhook_routes.py --cov=cellophanemail/routes/webhooks --cov-report=term-missing`
- [ ] Target: 80% coverage on `routes/webhooks.py`
- [ ] No linting errors: `ruff check tests/test_webhook_routes.py`

#### Manual Verification:
- [ ] Helper methods tested individually
- [ ] Error responses properly formatted
- [ ] Integration with routing service tested

---

## Testing Strategy

### Unit Test Principles

1. **Mock at boundaries**: Database, external APIs (Stripe, Postmark)
2. **Test behavior**: Use real JWT tokens, real data structures
3. **Use Protocol contracts**: Define and verify service interfaces
4. **Follow existing patterns**: JWT service tests are the gold standard

### Integration Test Approach

- Use AsyncTestClient for all route tests
- Mock only external services (Stripe, email providers)
- Test full request → service → response flow
- Verify authentication integration with real JWT tokens

### Coverage Measurement

```bash
# Run all tests with coverage
pytest --cov=cellophanemail --cov-report=html --cov-report=term-missing

# Phase-specific coverage
pytest tests/test_jwt_middleware.py --cov=cellophanemail/middleware/jwt_auth
pytest tests/test_billing_routes.py --cov=cellophanemail/routes/billing
pytest tests/test_email_routing_service.py --cov=cellophanemail/services/email_routing_service
```

### Verification Checklist Per Phase

**Before merging each phase**:
1. All tests pass: `pytest tests/test_<phase>.py -v`
2. Coverage target met for that component
3. No linting errors: `ruff check tests/`
4. Manual review of test quality (no shallow mocks)
5. Update phase checkbox in this plan

---

## Performance Considerations

- Tests should run fast (< 5 seconds per test file)
- Use function-scoped fixtures (fresh state per test)
- Avoid unnecessary database operations (mock when possible)
- Parallelize test execution: `pytest -n auto`

---

## Migration Notes

### Git Workflow Per Phase

```bash
# Phase 1 example:
git checkout -b test/phase-1-infrastructure
# ... implement tests ...
pytest tests/factories.py tests/helpers.py tests/assertions.py
git add tests/factories.py tests/helpers.py tests/assertions.py
git commit -m "test: Add test infrastructure (Phase 1)

- Create UserFactory, StripeFactory, JWTFactory
- Add create_mock_asgi_connection helper
- Add JWT and routing assertion helpers
- Standardize test patterns for subsequent phases"
git push origin test/phase-1-infrastructure
# Create PR, get review, merge

# Phase 2:
git checkout main && git pull
git checkout -b test/phase-2-jwt-middleware
# ... implement tests ...
```

### Handling Test Failures

If tests reveal bugs in implementation:
1. **Document the bug** in the test as a comment
2. **Create a ticket** for the bug fix
3. **Skip the test** temporarily: `@pytest.mark.skip(reason="Bug #123")`
4. **Continue with phase** - don't block on implementation bugs
5. **Fix bugs separately** in dedicated branches

---

## References

- Test Coverage Analysis: `thoughts/shared/research/2025-10-12-test-coverage-ci-cd-infrastructure.md`
- Test Distribution: `thoughts/shared/research/2025-10-12-test-distribution-workflow-analysis.md`
- Testing Philosophy: `thoughts/shared/til/2025-10-13-routes-services-middleware-architecture.md`
- Existing Test Patterns: `tests/test_jwt_service.py`, `tests/unit/test_component_contracts.py`

---

## Timeline Summary

| Phase | Duration | Week | Priority |
|-------|----------|------|----------|
| 1. Test Infrastructure | 2 days | 1 | Foundation |
| 2. JWT Middleware | 3 days | 1 | CRITICAL |
| 3. Billing Routes | 3 days | 2 | CRITICAL |
| 4. Email Routing Service | 4 days | 2-3 | CRITICAL |
| 5. User Service | 3 days | 3 | CRITICAL |
| 6. Auth Endpoints | 3 days | 4 | HIGH |
| 7. Webhook Routes | 2 days | 4 | HIGH |
| **Total** | **20 days (4 weeks)** | - | - |

**End Goal**: 80% overall coverage, 95% on security-critical components, reliable foundation for feature development.
