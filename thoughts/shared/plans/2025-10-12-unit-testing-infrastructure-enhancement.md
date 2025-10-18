# Unit Testing Infrastructure Enhancement Plan

**Date**: 2025-10-12
**Repository**: cellophanemail
**Status**: draft

## Overview

Enhance CellophoneMail's unit testing infrastructure to enable constructive feature development without needing to revert changes. This plan addresses critical test coverage gaps in authentication, billing, email processing, and security features to build a robust safety net for development.

## Current State Analysis

### What Exists Today

#### ✅ Strong Testing Foundation
- **Framework**: pytest + pytest-asyncio (348+ test functions across 39 files)
- **Test Organization**:
  - `tests/unit/` - 23 files with mocked dependencies
  - `tests/integration/` - 1 file (Stripe registration)
  - `tests/` root - 15 files (auth, email, Four Horsemen)
- **Fixtures**: Multi-level conftest.py with sophisticated fixtures
  - `test_client` - AsyncTestClient for API testing
  - `mock_settings` - Auto-applied to unit tests
  - Session-scoped event loop for async operations
- **Patterns**: Mature TDD practices (Arrange-Act-Assert, parametric testing, mock side effects)
- **Coverage Tools**: pytest-cov installed but no .coveragerc configuration

#### ❌ Critical Test Coverage Gaps

**Based on codebase analysis, approximately 3,500 lines of untested code across:**

1. **Authentication & Security (CRITICAL - Risk 9/10)**
   - JWT Auth Middleware: 100% untested (entire file)
   - Auth Routes: login, logout, dashboard, profile, refresh_token - NO TESTS
   - Webhook Validator: HMAC signature validation, replay detection - NO TESTS

2. **Billing & Payments (CRITICAL - Risk 10/10)**
   - Billing Routes: create_checkout, customer_portal - NO TESTS
   - Stripe Webhooks: Incomplete (missing edge cases, error paths)
   - Financial transactions without test coverage = unacceptable risk

3. **Email Processing (HIGH - Risk 7/10)**
   - Email Delivery Service: Postmark integration - NO TESTS
   - Email Routing Service: Validation pipeline - NO TESTS
   - Webhook Routes: Incomplete (missing domain validation, error handling)

4. **User Management (HIGH - Risk 7/10)**
   - User Service: Shield address creation, user lookup - NO TESTS
   - Shield Address Manager: Minimal tests (in-memory store, collision handling missing)

5. **Rate Limiting (HIGH - Risk 7/10)**
   - Rate Limiter: Redis backend, token bucket, sliding window algorithms - NO TESTS
   - Only basic in-memory backend tested

### Key Insights

**Strengths:**
- Excellent pytest configuration and fixture patterns
- Strong async testing support
- Good mocking patterns demonstrated in existing tests
- TDD practices visible in some test files

**Critical Issues:**
- ~57% of codebase untested (estimated 3,500 lines)
- Authentication and billing lack adequate coverage
- Error paths and edge cases rarely tested
- Integration between components minimally tested
- No coverage reporting configured

## Desired End State

### For Developers
- Write features with confidence using TDD approach
- Tests catch bugs before code review
- Fast feedback loop: Unit tests run in < 10 seconds
- Clear test patterns for every module type (routes, services, models)
- Coverage reports show gaps immediately

### For the Codebase
- **Minimum 80% test coverage** on critical paths:
  - Authentication: 95%+ coverage
  - Billing: 95%+ coverage
  - Email Processing: 85%+ coverage
  - Security: 90%+ coverage
- All public API endpoints have tests
- All error paths tested
- Edge cases covered with parametric tests
- Integration tests for critical user flows

### Verification Criteria
- ✅ All critical modules have >80% test coverage
- ✅ No pull request merged without tests for new code
- ✅ Coverage report generated on every test run
- ✅ Tests run in < 30 seconds (unit tests only)
- ✅ New developers can write tests following clear patterns
- ✅ Zero untested authentication or billing code

## What We're NOT Doing

**Explicitly Out of Scope:**
- ❌ Rewriting existing tests (keep all 348+ tests)
- ❌ Changing test framework (stay with pytest)
- ❌ End-to-end browser testing (no Selenium/Playwright)
- ❌ Performance/load testing
- ❌ Security scanning (separate tool)
- ❌ Test data generation frameworks (keep fixtures simple)
- ❌ Mutation testing
- ❌ Contract testing with external APIs

## Implementation Approach

**Strategy:** Test-Driven Development (TDD) for all new code, backfill critical gaps in existing code.

**Guiding Principles:**
1. **Test Critical Paths First**: Authentication and billing before anything else
2. **One Module at a Time**: Complete coverage for one module before moving on
3. **Follow Existing Patterns**: Use established fixture and mocking patterns
4. **Fast Tests**: Keep unit tests fast (<10s total) by proper mocking
5. **Document Patterns**: Create test template for each module type

---

## Phase 1: Foundation - Testing Infrastructure Setup

### Overview
Set up test coverage reporting, create test templates, and establish testing standards to guide all future test writing.

### Changes Required

#### 1.1 Configure Test Coverage Reporting

**File**: `.coveragerc` (NEW FILE)

```ini
[run]
source = src/cellophanemail
omit =
    */tests/*
    */conftest.py
    */__pycache__/*
    */site-packages/*
    */venv/*
    */.venv/*
    */migrations/*
    */plugins/smtp/__main__.py
    */app.py

branch = True
parallel = True

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    def __str__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
    @abc.abstractmethod
    class .*\bProtocol\):
    @overload
    except ImportError:
    raise NotImplementedError

precision = 2
show_missing = True
skip_covered = False
skip_empty = True

[html]
directory = htmlcov

[xml]
output = coverage.xml

[paths]
source =
    src/cellophanemail
    */cellophanemail
```

**Why this configuration:**
- Branch coverage tracks if-else paths
- Excludes test files, migrations, and entry points
- Generates HTML for local viewing and XML for CI/CD
- Shows missing lines to guide test writing

#### 1.2 Update pytest Configuration

**File**: `pytest.ini` (UPDATE)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Exclude directories from test discovery
norecursedirs = .git .github .pytest_cache htmlcov logs scripts thoughts

# Warning filters
filterwarnings =
    ignore::DeprecationWarning:dataclasses:
    ignore::DeprecationWarning:litestar:

# Asyncio mode (for pytest-asyncio)
asyncio_mode = auto

# Markers for test organization
markers =
    unit: Unit tests with mocked dependencies (fast)
    integration: Integration tests with external services
    critical: Tests for critical business logic (auth, billing)
    security: Security-related tests
    slow: Tests that take > 1 second
    wip: Work in progress tests (excluded by default)

# Coverage settings
addopts =
    --strict-markers
    --tb=short
    --disable-warnings
    -ra

# Minimum coverage threshold (fail if below)
# Enable after Phase 2
# --cov=src/cellophanemail
# --cov-report=html
# --cov-report=term-missing
# --cov-fail-under=80

[coverage:run]
source = src/cellophanemail
omit =
    */tests/*
    */conftest.py
    */__pycache__/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

**Why these updates:**
- Adds test markers for organization
- Strict markers prevent typos
- Coverage options commented out (enable after Phase 2)
- Short traceback for faster feedback

#### 1.3 Create Test Template Documentation

**File**: `docs/TESTING_PATTERNS.md` (NEW FILE)

```markdown
# Testing Patterns Guide

Complete guide to writing tests in CellophoneMail following established patterns.

## Test Structure

### Standard Test Structure (Arrange-Act-Assert)

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_function_success_case(self):
    """Test description of what this validates."""
    # Arrange - Set up test data and mocks
    input_data = {"key": "value"}
    expected_result = "expected"

    with patch('module.dependency') as mock_dep:
        mock_dep.return_value = "mocked_value"

        # Act - Execute the function being tested
        result = await function_under_test(input_data)

        # Assert - Verify results and mock calls
        assert result == expected_result
        mock_dep.assert_called_once_with(input_data)
```

## Test Types by Module

### 1. Testing Routes (API Endpoints)

**Pattern**: Use `test_client` fixture, mock services, verify HTTP responses.

**Template**:
```python
# tests/test_<module>_routes.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.unit
@pytest.mark.critical
class TestUserRoutes:
    """Test user management API routes."""

    @pytest.mark.asyncio
    async def test_get_profile_success(self, test_client):
        """Test successful user profile retrieval."""
        # Arrange
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"

        with patch('cellophanemail.routes.auth.get_current_user', return_value=mock_user):
            # Act
            async with test_client as client:
                response = await client.get(
                    "/auth/profile",
                    headers={"Authorization": "Bearer fake-token"}
                )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, test_client):
        """Test profile endpoint requires authentication."""
        # Act
        async with test_client as client:
            response = await client.get("/auth/profile")

        # Assert
        assert response.status_code == 401
```

**Key Points:**
- Mock authentication for protected endpoints
- Test both success and error cases
- Verify status codes and response structure
- Use descriptive test names

### 2. Testing Services

**Pattern**: Mock external dependencies (database, APIs), test business logic.

**Template**:
```python
# tests/test_<module>_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from cellophanemail.services.user_service import UserService


@pytest.mark.unit
class TestUserService:
    """Test UserService business logic."""

    @pytest.fixture
    def user_service(self):
        """Create UserService instance."""
        return UserService()

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service):
        """Test successful user creation."""
        # Arrange
        user_data = {
            "email": "new@example.com",
            "password": "SecurePass123!",
            "first_name": "Test"
        }

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = user_data["email"]

        with patch('cellophanemail.services.user_service.User') as MockUser:
            mock_save = AsyncMock()
            MockUser.return_value.save.return_value.run = mock_save
            MockUser.return_value = mock_user

            # Act
            result = await user_service.create_user(**user_data)

            # Assert
            assert result.id == "user-123"
            assert result.email == user_data["email"]
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service):
        """Test user creation fails with duplicate email."""
        # Arrange
        with patch('cellophanemail.services.user_service.User.exists') as mock_exists:
            mock_run = AsyncMock(return_value=True)
            mock_exists.return_value.where.return_value.run = mock_run

            # Act & Assert
            with pytest.raises(ValueError, match="Email already exists"):
                await user_service.create_user(
                    email="existing@example.com",
                    password="pass"
                )
```

**Key Points:**
- Mock database operations with AsyncMock
- Test business logic, not database
- Use pytest.raises for exception testing
- Mock complex query chains

### 3. Testing Middleware

**Pattern**: Mock request/response, test authentication flow.

**Template**:
```python
# tests/test_<module>_middleware.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from cellophanemail.middleware.jwt_auth import JWTAuthenticationMiddleware


@pytest.mark.unit
@pytest.mark.security
class TestJWTAuthMiddleware:
    """Test JWT authentication middleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return JWTAuthenticationMiddleware(app=MagicMock())

    @pytest.mark.asyncio
    async def test_authenticate_with_valid_token(self, middleware):
        """Test authentication succeeds with valid JWT."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {"authorization": "Bearer valid-token"}

        mock_user = MagicMock()
        mock_user.id = "user-123"

        with patch('cellophanemail.middleware.jwt_auth.verify_token', return_value=mock_user):
            # Act
            result = await middleware.authenticate_request(mock_connection)

            # Assert
            assert result == mock_user
            assert mock_connection.user == mock_user

    @pytest.mark.asyncio
    async def test_authenticate_missing_token(self, middleware):
        """Test authentication fails without token."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {}

        # Act
        result = await middleware.authenticate_request(mock_connection)

        # Assert
        assert result is None
```

**Key Points:**
- Mock Connection object
- Test token extraction from headers and cookies
- Verify user is set on connection
- Test missing/invalid token scenarios

### 4. Testing Webhooks

**Pattern**: Mock signature validation, test payload processing.

**Template**:
```python
# tests/test_<module>_webhooks.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.unit
@pytest.mark.critical
class TestStripeWebhooks:
    """Test Stripe webhook handling."""

    @pytest.mark.asyncio
    async def test_subscription_created_webhook(self, test_client):
        """Test subscription created event processing."""
        # Arrange
        webhook_payload = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "status": "active"
                }
            }
        }

        with patch('cellophanemail.routes.stripe_webhooks.stripe.Webhook.construct_event') as mock_verify:
            with patch('cellophanemail.routes.stripe_webhooks.User.objects') as mock_user:
                mock_verify.return_value = webhook_payload
                mock_user_instance = MagicMock()
                mock_user_instance.id = "user-123"
                mock_user.return_value.where.return_value.first.return_value.run = AsyncMock(
                    return_value=mock_user_instance
                )

                # Act
                async with test_client as client:
                    response = await client.post(
                        "/webhooks/stripe",
                        json=webhook_payload,
                        headers={"Stripe-Signature": "valid-sig"}
                    )

                # Assert
                assert response.status_code == 200
```

**Key Points:**
- Mock webhook signature validation
- Test each event type separately
- Verify database updates
- Test invalid signature rejection

## Mocking Patterns

### AsyncMock for Async Functions

```python
with patch('module.async_function', new=AsyncMock()) as mock:
    mock.return_value = "result"
```

### Mocking Database Queries

```python
# Piccolo ORM query chain
with patch('module.Model.objects') as mock_objects:
    mock_query = MagicMock()
    mock_query.first.return_value.run = AsyncMock(return_value=mock_data)
    mock_objects.return_value.where.return_value = mock_query
```

### Mocking External HTTP Calls

```python
with patch('httpx.AsyncClient') as mock_client_class:
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    mock_client.post.return_value = mock_response
    mock_client_class.return_value.__aenter__.return_value = mock_client
```

### Side Effects for Errors

```python
mock.side_effect = ValueError("Error message")
mock.side_effect = [result1, result2, Exception("Third call fails")]
```

## Parametric Testing

Use pytest.mark.parametrize for testing multiple inputs:

```python
@pytest.mark.parametrize("input,expected", [
    ("lowercase", "LOWERCASE"),
    ("UPPERCASE", "UPPERCASE"),
    ("MixedCase", "MIXEDCASE"),
    ("", ""),
])
def test_uppercase_conversion(input, expected):
    """Test string uppercase conversion."""
    assert input.upper() == expected
```

## Testing Edge Cases

Always test:
1. **Success case** - Happy path
2. **Invalid input** - Validation errors
3. **Missing data** - None, empty string, empty list
4. **Duplicate data** - Uniqueness constraints
5. **Not found** - Entity doesn't exist
6. **Unauthorized** - Permission denied
7. **External service failure** - API timeout, network error
8. **Database errors** - Connection failure, constraint violation

## Running Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest -m unit

# Critical tests (auth, billing)
pytest -m critical

# Specific file
pytest tests/test_user_service.py

# With coverage
pytest --cov=cellophanemail --cov-report=html

# Watch mode (requires pytest-watch)
ptw -m unit
```

## Coverage Goals

- **Critical modules** (auth, billing, security): 95%+
- **Business logic** (services, features): 85%+
- **Routes**: 80%+
- **Utilities**: 70%+

## Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive test names** - test_function_scenario_expectedResult
3. **Test isolation** - No shared state between tests
4. **Fast tests** - Mock everything external
5. **Readable tests** - Clear Arrange-Act-Assert structure
6. **Test behavior, not implementation** - Avoid testing private methods
7. **Use fixtures** - Reuse common setup
8. **Mark tests** - Use @pytest.mark.unit, @pytest.mark.critical

## Common Mistakes

❌ **Don't:**
- Test implementation details
- Use real database in unit tests
- Share state between tests
- Test framework code
- Make tests depend on execution order

✅ **Do:**
- Test public interfaces
- Mock external dependencies
- Use fixtures for common setup
- Test edge cases and errors
- Keep tests independent

## Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
```

#### 1.4 Create Test Command Scripts

**File**: `bin/test` (NEW FILE)

```bash
#!/usr/bin/env bash
# Comprehensive test execution script

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
MODE="all"
COVERAGE=false
VERBOSE=false
WATCH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit|-u)
            MODE="unit"
            shift
            ;;
        --critical|-c)
            MODE="critical"
            shift
            ;;
        --coverage|--cov)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --watch|-w)
            WATCH=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./bin/test [OPTIONS] [PYTEST_ARGS]"
            echo ""
            echo "Options:"
            echo "  --unit, -u         Run only unit tests (fast)"
            echo "  --critical, -c     Run only critical tests (auth, billing)"
            echo "  --coverage, --cov  Generate coverage report"
            echo "  --verbose, -v      Verbose output"
            echo "  --watch, -w        Watch mode (requires pytest-watch)"
            echo "  --help, -h         Show this help"
            echo ""
            echo "Examples:"
            echo "  ./bin/test                    # All tests"
            echo "  ./bin/test --unit             # Unit tests only"
            echo "  ./bin/test --coverage         # With coverage report"
            echo "  ./bin/test --watch --unit     # Watch unit tests"
            echo "  ./bin/test tests/test_auth.py # Specific file"
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

# Add marker filter
if [ "$MODE" = "unit" ]; then
    PYTEST_CMD="$PYTEST_CMD -m unit"
elif [ "$MODE" = "critical" ]; then
    PYTEST_CMD="$PYTEST_CMD -m critical"
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=cellophanemail --cov-report=html --cov-report=term-missing"
fi

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add any remaining arguments
PYTEST_CMD="$PYTEST_CMD $@"

# Watch mode
if [ "$WATCH" = true ]; then
    echo -e "${BLUE}🔍 Starting test watch mode...${NC}"
    ptw -- $PYTEST_CMD
    exit 0
fi

# Run tests
echo -e "${BLUE}🧪 Running tests...${NC}"
echo -e "${YELLOW}Command: $PYTEST_CMD${NC}"
echo ""

$PYTEST_CMD

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"

    if [ "$COVERAGE" = true ]; then
        echo -e "${YELLOW}📊 Coverage report: htmlcov/index.html${NC}"
    fi
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
fi

exit $EXIT_CODE
```

Make executable:
```bash
chmod +x bin/test
```

**Why this script:**
- Simple interface for common test scenarios
- Coverage report generation
- Watch mode for TDD workflow
- Filters by test type (unit, critical)

#### 1.5 Update Development Workflow Documentation

**File**: `docs/DEVELOPMENT_WORKFLOW.md` (UPDATE)

Add section on testing workflow:

```markdown
## Testing Workflow

### Before Starting Feature Development

1. **Write failing tests first** (TDD):
   ```bash
   # Create test file
   touch tests/test_new_feature.py

   # Write test for expected behavior
   # Test will fail (RED phase)
   ./bin/test tests/test_new_feature.py
   ```

2. **Implement feature** (GREEN phase):
   ```bash
   # Write minimal code to make test pass
   # Run tests frequently
   ./bin/test --watch tests/test_new_feature.py
   ```

3. **Refactor** (REFACTOR phase):
   ```bash
   # Improve code while tests stay green
   ./bin/test tests/test_new_feature.py
   ```

### During Development

**Fast Feedback Loop:**
```bash
# Watch mode - auto-run tests on file changes
./bin/test --watch --unit
```

**Check Coverage:**
```bash
# Run with coverage
./bin/test --unit --coverage

# View HTML report
open htmlcov/index.html

# Check specific module coverage
pytest --cov=cellophanemail.services.user_service --cov-report=term-missing
```

### Before Committing

**Run All Unit Tests:**
```bash
./bin/test --unit
# Should complete in < 10 seconds
```

**Run Critical Tests:**
```bash
./bin/test --critical
# Auth, billing, security tests
```

### Before Creating PR

**Full Test Suite:**
```bash
# All tests with coverage
./bin/test --coverage

# Ensure >80% coverage on changes
```

**Coverage Report:**
- Open `htmlcov/index.html`
- Check that new code is green (covered)
- Add tests for any red (uncovered) lines

### Test-Driven Development (TDD) Example

```python
# 1. RED - Write failing test
def test_calculate_discount():
    """Test discount calculation."""
    result = calculate_discount(price=100, discount_percent=20)
    assert result == 80

# Run test - FAILS (function doesn't exist)

# 2. GREEN - Minimal implementation
def calculate_discount(price, discount_percent):
    return price - (price * discount_percent / 100)

# Run test - PASSES

# 3. REFACTOR - Improve while tests pass
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price."""
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be 0-100")
    return price * (1 - discount_percent / 100)

# Add test for validation
def test_calculate_discount_invalid():
    with pytest.raises(ValueError):
        calculate_discount(100, 150)

# Run tests - BOTH PASS
```
```

### Success Criteria

#### Automated Verification:
- [ ] Coverage config exists: `test -f .coveragerc`
- [ ] pytest.ini updated with markers
- [ ] Test script is executable: `test -x bin/test`
- [ ] Coverage report generates: `pytest --cov=cellophanemail --cov-report=html && test -f htmlcov/index.html`
- [ ] Test patterns doc exists: `test -f docs/TESTING_PATTERNS.md`

#### Manual Verification:
- [ ] Run `./bin/test --unit` - completes in < 10 seconds
- [ ] Run `./bin/test --coverage` - generates HTML report
- [ ] Open `htmlcov/index.html` - shows current coverage
- [ ] Test patterns document is clear and comprehensive
- [ ] Developers can follow test templates to write new tests

---

## Phase 2: Critical Path Testing - Authentication & Security

### Overview
Achieve 95%+ test coverage on all authentication, JWT, and security-related code. These are the highest risk areas that must have comprehensive tests before any other work.

### Priority Order

1. JWT Auth Middleware (100% untested - CRITICAL)
2. Auth Routes (login, logout, profile, refresh - NO TESTS)
3. Webhook Validator (signature validation - NO TESTS)
4. JWT Service (blacklisting gaps)

### Changes Required

#### 2.1 Test JWT Auth Middleware

**File**: `tests/unit/test_jwt_auth_middleware.py` (NEW FILE)

**Test Cases to Implement (Est. 20 tests):**

```python
"""Comprehensive tests for JWT authentication middleware."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from litestar.connection import Request
from litestar.exceptions import NotAuthorizedException

from cellophanemail.middleware.jwt_auth import (
    JWTAuthenticationMiddleware,
    jwt_auth_required,
    create_auth_response,
    create_dual_auth_response
)


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.critical
class TestJWTAuthenticationMiddleware:
    """Test JWT authentication middleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return JWTAuthenticationMiddleware(app=MagicMock())

    # Token Extraction Tests
    @pytest.mark.asyncio
    async def test_extract_token_from_authorization_header(self, middleware):
        """Test token extracted from Authorization header."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {"authorization": "Bearer test-token-123"}
        mock_connection.cookies = {}

        # Act
        token = await middleware._extract_token_with_priority(mock_connection)

        # Assert
        assert token == "test-token-123"

    @pytest.mark.asyncio
    async def test_extract_token_from_cookie_fallback(self, middleware):
        """Test token extracted from cookie when header missing."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {}
        mock_connection.cookies = {"access_token": "cookie-token-456"}

        # Act
        token = await middleware._extract_token_with_priority(mock_connection)

        # Assert
        assert token == "cookie-token-456"

    @pytest.mark.asyncio
    async def test_extract_token_header_priority_over_cookie(self, middleware):
        """Test Authorization header takes priority over cookie."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {"authorization": "Bearer header-token"}
        mock_connection.cookies = {"access_token": "cookie-token"}

        # Act
        token = await middleware._extract_token_with_priority(mock_connection)

        # Assert
        assert token == "header-token"

    @pytest.mark.asyncio
    async def test_extract_token_returns_none_when_missing(self, middleware):
        """Test returns None when no token present."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {}
        mock_connection.cookies = {}

        # Act
        token = await middleware._extract_token_with_priority(mock_connection)

        # Assert
        assert token is None

    # Authentication Flow Tests
    @pytest.mark.asyncio
    async def test_authenticate_request_with_valid_token(self, middleware):
        """Test successful authentication with valid JWT."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {"authorization": "Bearer valid-token"}

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"

        with patch('cellophanemail.middleware.jwt_auth.verify_token') as mock_verify:
            mock_verify.return_value = mock_user

            # Act
            result = await middleware.authenticate_request(mock_connection)

            # Assert
            assert result == mock_user
            mock_verify.assert_called_once_with("valid-token", TokenType.ACCESS)

    @pytest.mark.asyncio
    async def test_authenticate_request_sets_user_on_connection(self, middleware):
        """Test user is set on connection after successful auth."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {"authorization": "Bearer token"}
        mock_user = MagicMock()

        with patch('cellophanemail.middleware.jwt_auth.verify_token', return_value=mock_user):
            # Act
            await middleware.authenticate_request(mock_connection)

            # Assert
            assert mock_connection.user == mock_user

    @pytest.mark.asyncio
    async def test_authenticate_request_returns_none_without_token(self, middleware):
        """Test authentication returns None when no token."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {}
        mock_connection.cookies = {}

        # Act
        result = await middleware.authenticate_request(mock_connection)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_request_handles_invalid_token(self, middleware):
        """Test invalid token returns None (doesn't raise)."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.headers = {"authorization": "Bearer invalid-token"}

        with patch('cellophanemail.middleware.jwt_auth.verify_token') as mock_verify:
            mock_verify.side_effect = JWTError("Invalid token")

            # Act
            result = await middleware.authenticate_request(mock_connection)

            # Assert
            assert result is None


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.critical
class TestJWTAuthRequired:
    """Test jwt_auth_required guard."""

    @pytest.mark.asyncio
    async def test_guard_allows_authenticated_user(self):
        """Test guard allows request with authenticated user."""
        # Arrange
        mock_connection = MagicMock()
        mock_user = MagicMock()
        mock_connection.user = mock_user

        # Act
        result = await jwt_auth_required(mock_connection, MagicMock())

        # Assert
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_guard_raises_without_user(self):
        """Test guard raises NotAuthorizedException without user."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.user = None

        # Act & Assert
        with pytest.raises(NotAuthorizedException):
            await jwt_auth_required(mock_connection, MagicMock())


@pytest.mark.unit
@pytest.mark.critical
class TestAuthResponseHelpers:
    """Test auth response creation helpers."""

    @pytest.mark.asyncio
    async def test_create_auth_response_generates_tokens(self):
        """Test auth response includes access and refresh tokens."""
        # Arrange
        user_id = "user-123"
        email = "test@example.com"

        with patch('cellophanemail.middleware.jwt_auth.create_access_token') as mock_access:
            with patch('cellophanemail.middleware.jwt_auth.create_refresh_token') as mock_refresh:
                mock_access.return_value = "access-token"
                mock_refresh.return_value = "refresh-token"

                # Act
                response = await create_auth_response(user_id, email)

                # Assert
                assert response.access_token == "access-token"
                assert response.refresh_token == "refresh-token"
                mock_access.assert_called_once_with(user_id=user_id, email=email)
                mock_refresh.assert_called_once_with(user_id=user_id, email=email)

    @pytest.mark.asyncio
    async def test_create_dual_auth_response_sets_cookies(self):
        """Test dual auth response sets httpOnly cookies."""
        # Arrange
        user_id = "user-123"
        email = "test@example.com"

        with patch('cellophanemail.middleware.jwt_auth.create_access_token', return_value="access"):
            with patch('cellophanemail.middleware.jwt_auth.create_refresh_token', return_value="refresh"):
                # Act
                response = await create_dual_auth_response(user_id, email, data={"user": "data"})

                # Assert
                assert "access_token" in response.cookies
                assert "refresh_token" in response.cookies

                # Verify cookie properties
                access_cookie = response.cookies["access_token"]
                assert access_cookie.httponly is True
                assert access_cookie.secure is True
                assert access_cookie.samesite == "lax"
```

**Estimated Effort**: 2-3 days to implement all 20 tests

#### 2.2 Test Auth Routes

**File**: `tests/unit/test_auth_routes_complete.py` (NEW FILE)

**Test Cases to Implement (Est. 30 tests):**

```python
"""Comprehensive tests for authentication routes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
@pytest.mark.critical
class TestLoginEndpoint:
    """Test /auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success_with_valid_credentials(self, test_client):
        """Test successful login with correct email/password."""
        # Arrange
        login_data = {
            "email": "user@example.com",
            "password": "CorrectPassword123!"
        }

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = login_data["email"]
        mock_user.hashed_password = "$2b$12$hashed_password"
        mock_user.is_active = True

        with patch('cellophanemail.routes.auth.User.objects') as mock_user_objects:
            with patch('cellophanemail.routes.auth.bcrypt.checkpw', return_value=True):
                with patch('cellophanemail.routes.auth.create_dual_auth_response') as mock_create_response:
                    # Setup database mock
                    mock_query = MagicMock()
                    mock_query.first.return_value.run = AsyncMock(return_value=mock_user)
                    mock_user_objects.return_value.where.return_value = mock_query

                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_create_response.return_value = mock_response

                    # Act
                    async with test_client as client:
                        response = await client.post("/auth/login", json=login_data)

                    # Assert
                    assert response.status_code == 200
                    mock_create_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_fails_with_wrong_password(self, test_client):
        """Test login fails with incorrect password."""
        # Arrange
        mock_user = MagicMock()
        mock_user.hashed_password = "$2b$12$hashed"

        with patch('cellophanemail.routes.auth.User.objects') as mock_objects:
            with patch('cellophanemail.routes.auth.bcrypt.checkpw', return_value=False):
                mock_query = MagicMock()
                mock_query.first.return_value.run = AsyncMock(return_value=mock_user)
                mock_objects.return_value.where.return_value = mock_query

                # Act
                async with test_client as client:
                    response = await client.post(
                        "/auth/login",
                        json={"email": "user@example.com", "password": "wrong"}
                    )

                # Assert
                assert response.status_code == 401
                data = response.json()
                assert "Invalid credentials" in data["error"]

    @pytest.mark.asyncio
    async def test_login_fails_with_nonexistent_user(self, test_client):
        """Test login fails when user doesn't exist."""
        # Arrange
        with patch('cellophanemail.routes.auth.User.objects') as mock_objects:
            mock_query = MagicMock()
            mock_query.first.return_value.run = AsyncMock(return_value=None)
            mock_objects.return_value.where.return_value = mock_query

            # Act
            async with test_client as client:
                response = await client.post(
                    "/auth/login",
                    json={"email": "nonexistent@example.com", "password": "pass"}
                )

            # Assert
            assert response.status_code == 401

    # Additional tests for:
    # - Inactive user login attempt
    # - Database query failure
    # - Malformed email
    # - Empty password
    # - Cookie setting verification


@pytest.mark.unit
@pytest.mark.critical
class TestLogoutEndpoint:
    """Test /auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_blacklists_token(self, test_client):
        """Test logout blacklists the access token."""
        # Arrange
        mock_user = MagicMock()
        mock_user.id = "user-123"

        with patch('cellophanemail.routes.auth.get_current_user', return_value=mock_user):
            with patch('cellophanemail.routes.auth.blacklist_token') as mock_blacklist:
                mock_blacklist.return_value = AsyncMock()

                # Act
                async with test_client as client:
                    response = await client.post(
                        "/auth/logout",
                        headers={"Authorization": "Bearer token-to-blacklist"}
                    )

                # Assert
                assert response.status_code == 200
                mock_blacklist.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_clears_cookies(self, test_client):
        """Test logout response clears auth cookies."""
        # Arrange
        with patch('cellophanemail.routes.auth.get_current_user', return_value=MagicMock()):
            with patch('cellophanemail.routes.auth.blacklist_token', new=AsyncMock()):
                # Act
                async with test_client as client:
                    response = await client.post(
                        "/auth/logout",
                        headers={"Authorization": "Bearer token"}
                    )

                # Assert
                assert response.status_code == 200
                # Verify cookies are cleared (max_age=0)
                cookies = response.cookies
                assert "access_token" in cookies
                assert cookies["access_token"].max_age == 0

    # Additional tests for:
    # - Logout without token (should succeed)
    # - Logout with already blacklisted token
    # - Token extraction from cookie vs header


@pytest.mark.unit
@pytest.mark.critical
class TestDashboardEndpoint:
    """Test /auth/dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_returns_user_data(self, test_client):
        """Test dashboard returns user information."""
        # Arrange
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"

        with patch('cellophanemail.routes.auth.get_current_user', return_value=mock_user):
            with patch('cellophanemail.routes.auth.generate_shield_email') as mock_shield:
                mock_shield.return_value = "shield@cellophanemail.com"

                # Act
                async with test_client as client:
                    response = await client.get(
                        "/auth/dashboard",
                        headers={"Authorization": "Bearer token"}
                    )

                # Assert
                assert response.status_code == 200
                data = response.json()
                assert data["user"]["email"] == "test@example.com"
                assert "protected_emails" in data

    # Additional tests for:
    # - User not found scenario
    # - Shield address generation
    # - Protected emails mock data
    # - Database query failure


# Add similar comprehensive test classes for:
# - TestRefreshTokenEndpoint (10+ tests)
# - TestGetProfileEndpoint (5+ tests)
```

**Estimated Effort**: 4-5 days to implement all 30 tests

#### 2.3 Test Webhook Validator

**File**: `tests/unit/test_webhook_validator.py` (NEW FILE)

**Test Cases to Implement (Est. 15 tests):**

```python
"""Tests for webhook signature validation."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from cellophanemail.features.security.webhook_validator import WebhookValidator


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.critical
class TestWebhookValidator:
    """Test webhook signature validation."""

    @pytest.fixture
    def validator(self):
        """Create validator with test secret."""
        return WebhookValidator(secret="test-secret-key")

    def test_create_signature(self, validator):
        """Test HMAC signature generation."""
        # Arrange
        payload = b'{"key": "value"}'
        timestamp = "1234567890"

        # Act
        signature = validator.create_signature(payload, timestamp)

        # Assert
        assert signature is not None
        assert len(signature) == 64  # SHA-256 hex digest length

    def test_validate_signature_success(self, validator):
        """Test valid signature passes validation."""
        # Arrange
        payload = b'{"key": "value"}'
        timestamp = str(int(datetime.now().timestamp()))
        signature = validator.create_signature(payload, timestamp)

        sig_header = f"t={timestamp},s={signature}"

        # Act
        is_valid = validator.validate_signature(payload, sig_header)

        # Assert
        assert is_valid is True

    def test_validate_signature_fails_with_wrong_signature(self, validator):
        """Test invalid signature fails validation."""
        # Arrange
        payload = b'{"key": "value"}'
        timestamp = str(int(datetime.now().timestamp()))
        sig_header = f"t={timestamp},s=wrong_signature"

        # Act
        is_valid = validator.validate_signature(payload, sig_header)

        # Assert
        assert is_valid is False

    def test_validate_signature_fails_with_expired_timestamp(self, validator):
        """Test signature fails if timestamp too old."""
        # Arrange
        payload = b'{"key": "value"}'
        old_timestamp = str(int((datetime.now() - timedelta(minutes=10)).timestamp()))
        signature = validator.create_signature(payload, old_timestamp)
        sig_header = f"t={old_timestamp},s={signature}"

        # Act
        is_valid = validator.validate_signature(payload, sig_header, max_age=300)  # 5 minutes

        # Assert
        assert is_valid is False

    def test_validate_signature_rejects_replay_attack(self, validator):
        """Test same signature can't be used twice."""
        # Arrange
        payload = b'{"key": "value"}'
        timestamp = str(int(datetime.now().timestamp()))
        signature = validator.create_signature(payload, timestamp)
        sig_header = f"t={timestamp},s={signature}"

        # Act - First validation
        first_valid = validator.validate_signature(payload, sig_header)

        # Act - Second validation (replay)
        second_valid = validator.validate_signature(payload, sig_header)

        # Assert
        assert first_valid is True
        assert second_valid is False  # Replay detected

    def test_validate_signature_rejects_oversized_payload(self, validator):
        """Test validation fails for payloads exceeding size limit."""
        # Arrange
        large_payload = b"x" * (5 * 1024 * 1024 + 1)  # > 5MB
        timestamp = str(int(datetime.now().timestamp()))
        sig_header = f"t={timestamp},s=fake_signature"

        # Act
        is_valid = validator.validate_signature(large_payload, sig_header)

        # Assert
        assert is_valid is False

    def test_signature_caching(self, validator):
        """Test validated signatures are cached."""
        # Arrange
        payload = b'{"key": "value"}'
        timestamp = str(int(datetime.now().timestamp()))
        signature = validator.create_signature(payload, timestamp)
        sig_header = f"t={timestamp},s={signature}"

        # Act
        validator.validate_signature(payload, sig_header)

        # Assert - Signature should be in cache
        assert len(validator._validated_signatures) > 0

    # Additional tests for:
    # - Malformed signature header
    # - Missing timestamp
    # - Invalid timestamp format
    # - Constant-time comparison (timing attack prevention)
    # - Key rotation
```

**Estimated Effort**: 2-3 days to implement all 15 tests

#### 2.4 Complete JWT Service Tests

**File**: `tests/test_jwt_service.py` (UPDATE - add missing tests)

Add tests for:
- Token blacklisting with Redis
- `refresh_access_token()` error paths
- User not found scenarios
- Database lookup failures

**Estimated Effort**: 1 day to add ~10 missing tests

### Success Criteria

#### Automated Verification:
- [ ] JWT Auth Middleware: 100% coverage: `pytest --cov=cellophanemail.middleware.jwt_auth --cov-report=term-missing tests/unit/test_jwt_auth_middleware.py`
- [ ] Auth Routes: >95% coverage: `pytest --cov=cellophanemail.routes.auth --cov-report=term-missing tests/unit/test_auth_routes_complete.py`
- [ ] Webhook Validator: >90% coverage: `pytest --cov=cellophanemail.features.security.webhook_validator --cov-report=term-missing tests/unit/test_webhook_validator.py`
- [ ] All critical security tests pass: `./bin/test -m critical`
- [ ] Tests run in < 15 seconds: `time ./bin/test -m critical`

#### Manual Verification:
- [ ] Can run critical tests: `./bin/test -m critical`
- [ ] All authentication edge cases covered
- [ ] Error handling validated for every auth endpoint
- [ ] Security vulnerabilities prevented by tests (replay attacks, timing attacks, etc.)
- [ ] Test output is clear and actionable

**Estimated Total Time for Phase 2**: 2-3 weeks

---

## Phase 3: Billing & Payments Testing

### Overview
Achieve 95%+ test coverage on all billing, Stripe integration, and payment-related code. Financial transactions require the highest level of testing confidence.

### Priority Order

1. Billing Routes (NO TESTS - CRITICAL)
2. Stripe Webhooks (INCOMPLETE - complete edge cases)
3. Stripe Service (GOOD - verify completeness)

### Changes Required

#### 3.1 Test Billing Routes

**File**: `tests/unit/test_billing_routes.py` (NEW FILE)

**Test Cases to Implement (Est. 25 tests):**

```python
"""Comprehensive tests for billing routes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
@pytest.mark.critical
class TestCreateCheckoutEndpoint:
    """Test /billing/create-checkout endpoint."""

    @pytest.mark.asyncio
    async def test_create_checkout_creates_stripe_customer_if_missing(self, test_client):
        """Test checkout creates Stripe customer for new users."""
        # Arrange
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.stripe_customer_id = None  # No existing customer
        mock_user.save = AsyncMock()

        mock_customer = MagicMock()
        mock_customer.id = "cus_new123"

        checkout_data = {"price_id": "price_123"}

        with patch('cellophanemail.routes.billing.get_current_user', return_value=mock_user):
            with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
                mock_stripe = MockStripeService.return_value
                mock_stripe.create_customer = AsyncMock(return_value=mock_customer)
                mock_stripe.create_checkout_session = AsyncMock(return_value=MagicMock(url="https://checkout.stripe.com/123"))

                # Act
                async with test_client as client:
                    response = await client.post(
                        "/billing/create-checkout",
                        json=checkout_data,
                        headers={"Authorization": "Bearer token"}
                    )

                # Assert
                assert response.status_code == 200
                assert mock_user.stripe_customer_id == "cus_new123"
                mock_user.save.assert_called_once()
                mock_stripe.create_customer.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_checkout_uses_existing_customer(self, test_client):
        """Test checkout uses existing Stripe customer ID."""
        # Arrange
        mock_user = MagicMock()
        mock_user.stripe_customer_id = "cus_existing"
        mock_user.save = AsyncMock()

        with patch('cellophanemail.routes.billing.get_current_user', return_value=mock_user):
            with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
                mock_stripe = MockStripeService.return_value
                mock_stripe.create_checkout_session = AsyncMock(
                    return_value=MagicMock(url="https://checkout.stripe.com/456")
                )

                # Act
                async with test_client as client:
                    response = await client.post(
                        "/billing/create-checkout",
                        json={"price_id": "price_123"},
                        headers={"Authorization": "Bearer token"}
                    )

                # Assert
                mock_stripe.create_customer.assert_not_called()
                mock_user.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_checkout_handles_stripe_api_error(self, test_client):
        """Test checkout handles Stripe API failures gracefully."""
        # Arrange
        mock_user = MagicMock()
        mock_user.stripe_customer_id = "cus_123"

        with patch('cellophanemail.routes.billing.get_current_user', return_value=mock_user):
            with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
                mock_stripe = MockStripeService.return_value
                mock_stripe.create_checkout_session = AsyncMock(
                    side_effect=stripe.error.StripeError("API Error")
                )

                # Act
                async with test_client as client:
                    response = await client.post(
                        "/billing/create-checkout",
                        json={"price_id": "price_123"},
                        headers={"Authorization": "Bearer token"}
                    )

                # Assert
                assert response.status_code == 500
                data = response.json()
                assert "error" in data

    # Additional tests for:
    # - Invalid price_id validation
    # - Unauthorized access (no auth token)
    # - Trial period customization
    # - Success/cancel URL generation
    # - Customer creation failure handling
    # - Database save failure


@pytest.mark.unit
@pytest.mark.critical
class TestCustomerPortalEndpoint:
    """Test /billing/portal endpoint."""

    @pytest.mark.asyncio
    async def test_customer_portal_creates_session(self, test_client):
        """Test portal endpoint creates Stripe portal session."""
        # Arrange
        mock_user = MagicMock()
        mock_user.stripe_customer_id = "cus_123"

        mock_portal_session = MagicMock()
        mock_portal_session.url = "https://billing.stripe.com/session/123"

        with patch('cellophanemail.routes.billing.get_current_user', return_value=mock_user):
            with patch('cellophanemail.routes.billing.StripeService') as MockStripeService:
                mock_stripe = MockStripeService.return_value
                mock_stripe.create_portal_session = AsyncMock(return_value=mock_portal_session)

                # Act
                async with test_client as client:
                    response = await client.get(
                        "/billing/portal",
                        headers={"Authorization": "Bearer token"}
                    )

                # Assert
                assert response.status_code == 200
                data = response.json()
                assert data["portal_url"] == "https://billing.stripe.com/session/123"

    @pytest.mark.asyncio
    async def test_customer_portal_requires_stripe_customer(self, test_client):
        """Test portal fails if user has no Stripe customer ID."""
        # Arrange
        mock_user = MagicMock()
        mock_user.stripe_customer_id = None

        with patch('cellophanemail.routes.billing.get_current_user', return_value=mock_user):
            # Act
            async with test_client as client:
                response = await client.get(
                    "/billing/portal",
                    headers={"Authorization": "Bearer token"}
                )

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "No Stripe customer" in data["error"]

    # Additional tests for:
    # - Portal session creation failure
    # - Return URL configuration
    # - Unauthorized access
```

**Estimated Effort**: 3-4 days to implement all 25 tests

#### 3.2 Complete Stripe Webhooks Tests

**File**: `tests/unit/test_stripe_webhooks.py` (UPDATE - add missing tests)

Add ~15 additional tests for:
- Unknown event types
- Malformed payloads
- Signature verification edge cases
- Database failures during event processing
- Timestamp conversion errors
- Concurrent event handling
- User/Subscription not found scenarios

**Estimated Effort**: 2-3 days to add missing tests

#### 3.3 Verify Stripe Service Coverage

**File**: `tests/unit/test_stripe_service.py` (VERIFY/UPDATE)

Ensure complete coverage (already has 15 tests):
- Add any missing error scenarios
- Verify all methods tested
- Check edge cases covered

**Estimated Effort**: 1 day to verify/add missing tests

### Success Criteria

#### Automated Verification:
- [ ] Billing Routes: 95%+ coverage: `pytest --cov=cellophanemail.routes.billing --cov-report=term-missing tests/unit/test_billing_routes.py`
- [ ] Stripe Webhooks: 95%+ coverage: `pytest --cov=cellophanemail.routes.stripe_webhooks --cov-report=term-missing tests/unit/test_stripe_webhooks.py`
- [ ] Stripe Service: 95%+ coverage (already achieved, verify)
- [ ] All billing tests pass: `./bin/test tests/unit/test_billing* tests/unit/test_stripe*`
- [ ] Tests run fast: `time ./bin/test tests/unit/test_billing* tests/unit/test_stripe*` < 10 seconds

#### Manual Verification:
- [ ] All Stripe integration points tested
- [ ] Financial transaction flows validated
- [ ] Error handling prevents payment issues
- [ ] Edge cases don't allow corrupted billing state
- [ ] Webhook events all handled correctly

**Estimated Total Time for Phase 3**: 2 weeks

---

## Phase 4: Email Processing & User Management

### Overview
Test core email processing, delivery, routing, and user/shield address management to ensure reliable email handling.

### Priority Order

1. Email Delivery Service (NO TESTS)
2. Email Routing Service (NO TESTS)
3. User Service (NO TESTS)
4. Webhook Routes (INCOMPLETE)
5. Shield Address Manager (MINIMAL TESTS)

### Changes Required

#### 4.1 Test Email Delivery Service

**File**: `tests/unit/test_email_delivery_service.py` (NEW FILE)

**Test Cases**: ~20 tests covering Postmark integration, SMTP fallback, error handling

**Estimated Effort**: 3 days

#### 4.2 Test Email Routing Service

**File**: `tests/unit/test_email_routing_service.py` (NEW FILE)

**Test Cases**: ~15 tests covering validation pipeline, domain validation, user lookup

**Estimated Effort**: 2-3 days

#### 4.3 Test User Service

**File**: `tests/unit/test_user_service_complete.py` (NEW FILE)

**Test Cases**: ~25 tests covering user creation, shield address management, user lookup

**Estimated Effort**: 3-4 days

#### 4.4 Complete Webhook Routes Tests

**File**: `tests/unit/test_webhook_routes_complete.py` (NEW FILE)

**Test Cases**: ~15 tests covering domain validation, error handling, strategy manager integration

**Estimated Effort**: 2 days

#### 4.5 Complete Shield Address Manager Tests

**File**: `tests/unit/test_shield_address_manager.py` (UPDATE/NEW)

**Test Cases**: ~10 tests covering in-memory store, collision handling, deactivation

**Estimated Effort**: 2 days

### Success Criteria

#### Automated Verification:
- [ ] Email Delivery: >85% coverage
- [ ] Email Routing: >85% coverage
- [ ] User Service: >85% coverage
- [ ] Webhook Routes: >85% coverage
- [ ] Shield Manager: >85% coverage

#### Manual Verification:
- [ ] Email processing flows tested end-to-end
- [ ] Error recovery paths validated
- [ ] External API failures handled gracefully

**Estimated Total Time for Phase 4**: 3 weeks

---

## Phase 5: Rate Limiting & Remaining Features

### Overview
Complete testing for rate limiting, remaining features, and integration tests.

### Priority Order

1. Rate Limiter (INCOMPLETE)
2. Processing Strategy Manager
3. Frontend Routes
4. Integration Tests (cross-component flows)

### Changes Required

(Similar detailed breakdown as previous phases)

**Estimated Total Time for Phase 5**: 2-3 weeks

---

## Testing Best Practices

### Test-Driven Development (TDD)

**Red-Green-Refactor Cycle:**

1. **RED**: Write failing test
   ```bash
   # Create test file
   touch tests/test_new_feature.py
   # Write test
   ./bin/test tests/test_new_feature.py
   # Test fails (expected)
   ```

2. **GREEN**: Make test pass
   ```bash
   # Implement minimal code
   # Watch tests
   ./bin/test --watch tests/test_new_feature.py
   ```

3. **REFACTOR**: Improve code
   ```bash
   # Refactor while tests stay green
   ./bin/test tests/test_new_feature.py
   ```

### Coverage-Driven Development

**Use coverage to guide testing:**

```bash
# Check coverage
pytest --cov=cellophanemail.services.new_service --cov-report=html

# Open report
open htmlcov/index.html

# Find red lines (untested)
# Write tests for uncovered lines
# Repeat until green
```

### Test Organization

**Organize by module type:**
- `tests/unit/test_<module>_routes.py` - API endpoints
- `tests/unit/test_<module>_service.py` - Business logic
- `tests/unit/test_<module>_middleware.py` - Middleware
- `tests/unit/test_<module>_webhooks.py` - Webhook handlers
- `tests/integration/test_<feature>_flow.py` - Integration tests

### Running Tests Efficiently

```bash
# Fast feedback during development
./bin/test --watch --unit

# Before committing
./bin/test --unit

# Before PR
./bin/test --coverage

# Run specific module
./bin/test tests/unit/test_auth_service.py
```

## Timeline Summary

| Phase | Duration | Key Deliverable | Tests Added |
|-------|----------|-----------------|-------------|
| Phase 1: Foundation | 1 week | Coverage config, test templates, docs | 0 (infrastructure) |
| Phase 2: Auth & Security | 2-3 weeks | JWT, auth routes, webhook validator | ~65 tests |
| Phase 3: Billing & Payments | 2 weeks | Billing routes, Stripe webhooks | ~40 tests |
| Phase 4: Email & User Mgmt | 3 weeks | Email delivery, routing, user service | ~85 tests |
| Phase 5: Rate Limiting & Rest | 2-3 weeks | Rate limiter, integration tests | ~60 tests |

**Total Estimated Time**: 10-12 weeks

**Total Tests Added**: ~250 tests (bringing total from 348 to ~600)

## Open Questions

1. **Coverage Threshold**: Should we enforce minimum coverage in CI/CD? (Recommendation: 80% after Phase 3)

2. **Test Data Factories**: Should we introduce factory_boy for test data? (Recommendation: Start with simple fixtures, add if needed)

3. **Contract Testing**: Should we add Pact for external API contracts? (Recommendation: Future enhancement)

4. **Mutation Testing**: Should we add mutation testing (mutmut, cosmic-ray)? (Recommendation: After 80% coverage achieved)

5. **Performance Testing**: When should we add load/stress tests? (Recommendation: Separate project after functional tests complete)

6. **Visual Regression**: Should we add visual testing for frontend? (Recommendation: Out of scope for unit testing plan)

## References

### Internal Documentation
- `docs/TESTING_STRATEGY.md` - Current testing strategy
- `docs/TESTING_WITHOUT_QUOTA.md` - Dry-run mode
- Existing tests in `tests/` directory (348+ tests)

### Test Infrastructure
- `pytest.ini` - Pytest configuration
- `conftest.py` - Root fixtures
- `tests/conftest.py` - Test fixtures
- `tests/unit/conftest.py` - Unit test mocks

### External Resources
- pytest documentation: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- Coverage.py: https://coverage.readthedocs.io/

---

**End of Implementation Plan**
