---
date: 2025-10-13T11:30:00+0000
author: Claude
topic: "Routes vs Services vs Middleware: Architectural Separation of Concerns"
tags: [til, architecture, design-patterns, separation-of-concerns, litestar, mvc]
related_files: [routes/auth.py, services/auth_service.py, middleware/jwt_auth.py]
---

# TIL: Routes vs Services vs Middleware - Architectural Differences

**Date**: 2025-10-13
**Context**: Understanding why CellophoneMail's codebase separates routes/, services/, and middleware/ and how they interact.

## The Three Layers

### 1. Routes/ - HTTP Interface Layer (Controllers)

**Purpose**: Handle HTTP requests and responses

**Responsibilities**:
- Define API endpoints (`@post("/register")`, `@get("/login")`)
- Parse request data (query params, JSON body, headers, cookies)
- Validate input using Pydantic models (`UserRegistration`, `UserLogin`)
- Call service layer functions to perform business logic
- Format responses and set HTTP status codes
- Handle HTTP-specific concerns (cookies, redirects, templates)

**Example** - `routes/auth.py:154-217`:
```python
@post("/register", status_code=HTTP_201_CREATED)
async def register_user(self, data: UserRegistration) -> Response[Dict[str, Any]]:
    # 1. Validate email uniqueness (calls service)
    is_unique = await validate_email_unique(data.email)

    # 2. Create user (calls service)
    user = await create_user(email=data.email, password=data.password)

    # 3. Create Stripe customer (calls service)
    customer = await stripe_service.create_customer(user_id=str(user.id))

    # 4. Format HTTP response
    return Response(content={"status": "registered", ...}, status_code=HTTP_201_CREATED)
```

**Key Characteristics**:
- **Thin controllers** - orchestrate service calls but contain minimal logic
- **HTTP-aware** - know about Request, Response, status codes
- **Route-specific** - each endpoint handles one HTTP operation
- **Testability**: Requires AsyncTestClient or request mocking

---

### 2. Services/ - Business Logic Layer

**Purpose**: Contain reusable business logic and data operations

**Responsibilities**:
- Implement core business operations (password hashing, user creation, email routing)
- Database queries and data persistence
- Complex algorithms and calculations
- Coordinate between models and external systems
- Provide reusable functions that routes (or other services) can call
- **No HTTP concerns** - services don't know about requests/responses

**Example** - `services/auth_service.py:10-25`:
```python
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')
```

**Example** - `services/email_routing_service.py:36-76`:
```python
async def validate_and_route_email(self, shield_address: str) -> EmailRoutingContext:
    """Orchestrate routing validation pipeline.

    Returns EmailRoutingContext (not HTTP response)
    """
    # 1. Domain validation
    if not self._validate_domain(context):
        return context

    # 2. User lookup
    if not await self._lookup_user(context):
        return context

    # 3. Status verification
    if not self._verify_user_active(context):
        return context

    return context
```

**Key Characteristics**:
- **Framework-agnostic** - work with data structures, not HTTP primitives
- **Reusable** - same function can be called from multiple routes or background jobs
- **Pure business logic** - hashing, validation, orchestration
- **Testability**: Easy to test in isolation with plain function calls

---

### 3. Middleware/ - Request/Response Interceptors

**Purpose**: Process every request before it reaches routes, and every response before it's returned

**Responsibilities**:
- Authentication and authorization (verify JWT tokens)
- Cross-cutting concerns that apply to many routes
- Request preprocessing (extract auth tokens, log requests, CORS)
- Response post-processing (add security headers, set cookies)
- Execute **before** route handlers run
- Can modify or reject requests before they reach routes

**Example** - `middleware/jwt_auth.py:38-76`:
```python
class JWTAuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        """Runs on EVERY request before route handler."""

        # 1. Extract token from Authorization header OR cookie
        token = self._extract_token_with_priority(connection)

        if not token:
            # Return empty auth result (allows anonymous requests)
            return AuthenticationResult(user=None, auth=None)

        # 2. Verify token validity
        payload = await verify_token(token, TokenType.ACCESS)

        # 3. Create user object
        user = await JWTUser.from_token_payload(payload)

        # 4. Attach user to request (available as request.user in routes)
        return AuthenticationResult(user=user, auth=token)
```

**Guard Function** - `middleware/jwt_auth.py:104-117`:
```python
def jwt_auth_required(connection: ASGIConnection, route_handler) -> None:
    """Guard function to require JWT authentication on specific routes."""
    user = connection.user  # Set by middleware above

    if not user or not isinstance(user, JWTUser):
        raise NotAuthorizedException("Authentication required")
```

**Usage in Route** - `routes/auth.py:101`:
```python
@get("/dashboard", guards=[jwt_auth_required])
async def dashboard(self, request: Request) -> Template:
    # Middleware already verified token and set request.user
    jwt_user = request.user  # Guaranteed to exist due to guard

    # Fetch full user data
    user = await User.objects().where(User.id == jwt_user.id).first()

    return Template(template_name="dashboard.html", context={"user": user})
```

**Key Characteristics**:
- **Global or guarded** - runs on every request OR on specific routes via guards
- **Cross-cutting** - authentication, logging, CORS apply to many routes
- **Request enrichment** - adds data to request before routes see it
- **Testability**: Hardest to test - requires mocking ASGI connections

---

## Complete Request Flow Example

Here's how a protected request flows through all three layers:

```
┌─────────────────────────────────────────────┐
│  1. HTTP REQUEST                            │
│     GET /auth/profile                       │
│     Authorization: Bearer <jwt_token>       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  2. MIDDLEWARE (jwt_auth.py)                │
│     - Extract token from header             │
│     - Verify token with jwt_service         │
│     - Create JWTUser object                 │
│     - Set request.user = JWTUser(...)       │
│                                             │
│  Middleware runs BEFORE route handler       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  3. GUARD CHECK (jwt_auth_required)         │
│     - Check if request.user exists          │
│     - Raise NotAuthorizedException if None  │
│                                             │
│  Guards run AFTER middleware                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  4. ROUTE HANDLER (routes/auth.py:264-296)  │
│     - Access: jwt_user = request.user       │
│     - Call service to get full user data    │
│     - Format JSON response                  │
│                                             │
│  Route orchestrates service calls           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  5. SERVICE LAYER (services/...)            │
│     - user = User.objects().where(...)      │
│     - Database query                        │
│     - Return User object                    │
│                                             │
│  Services contain business logic            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  6. HTTP RESPONSE                           │
│     200 OK                                  │
│     {                                       │
│       "user_id": "123",                     │
│       "email": "user@example.com",          │
│       "shield_address": "user123@..."       │
│     }                                       │
└─────────────────────────────────────────────┘
```

---

## Why This Separation Matters

### 1. **Testability**

From CellophoneMail's test coverage analysis (2025-10-12):

| Layer | Testability | Current Coverage | Example |
|-------|-------------|------------------|---------|
| **Services** | ✅ **Easiest** | 37 auth tests, 18 billing tests | `test_auth_service.py` - 21 tests |
| **Routes** | ⚠️ **Moderate** | ~20 route tests total | `routes/billing.py` - **0 tests** ❌ |
| **Middleware** | ❌ **Hardest** | **0 middleware tests** | `middleware/jwt_auth.py` - **0 tests** ❌ |

**Why Services Are Easiest to Test**:
```python
# No HTTP mocking needed - just call the function
def test_hash_password():
    hashed = hash_password("mypassword123")
    assert len(hashed) > 0
    assert verify_password("mypassword123", hashed) == True
```

**Why Routes Are Harder**:
```python
# Need AsyncTestClient and request mocking
async def test_register_endpoint():
    async with AsyncTestClient(app=app) as client:
        response = await client.post("/auth/register", json={...})
        assert response.status_code == 201
```

**Why Middleware Is Hardest**:
```python
# Need to mock ASGI connections, simulate token extraction
async def test_jwt_middleware():
    connection = create_mock_asgi_connection(headers={"Authorization": "Bearer ..."})
    result = await middleware.authenticate_request(connection)
    assert result.user is not None
```

### 2. **Reusability**

**Services Can Be Called From Multiple Places**:
- `hash_password()` used in:
  - Registration endpoint (`routes/auth.py:154`)
  - Password reset endpoint (future)
  - Admin user creation (future)
  - Background job for password migration (future)

- `email_routing_service.validate_and_route_email()` used in:
  - Postmark webhook route (`routes/webhooks.py:36`)
  - Gmail webhook route (`routes/webhooks.py:106`)
  - Background email processor (future)
  - Testing/admin tools (future)

**Middleware Applies to Many Routes Automatically**:
```python
# JWT middleware runs on ALL requests
app = Litestar(
    middleware=[JWTAuthenticationMiddleware],
    route_handlers=[AuthController, BillingController, ...]
)

# Guards protect specific routes
@get("/dashboard", guards=[jwt_auth_required])  # Protected
@get("/pricing")                                 # Public
```

### 3. **Maintainability**

**Change JWT Algorithm? Only Update One Place**:
- ❌ **Without separation**: Update token logic in every route (20+ places)
- ✅ **With separation**: Update `services/jwt_service.py` (1 place)

**Add Logging to All Routes? Add Middleware**:
```python
class LoggingMiddleware:
    async def __call__(self, request, call_next):
        logger.info(f"{request.method} {request.url}")
        response = await call_next(request)
        return response

# Automatically logs ALL requests
```

### 4. **Separation of Concerns**

**Each Layer Has One Job**:

| Layer | Responsibility | Doesn't Care About |
|-------|---------------|-------------------|
| **Routes** | HTTP interface | How passwords are hashed |
| **Services** | Business logic | HTTP status codes, cookies |
| **Middleware** | Request processing | Individual endpoint logic |

**Example - Changing Response Format**:
- Want to add `api_version` to all responses?
- ❌ **Without separation**: Update every route handler (50+ places)
- ✅ **With separation**: Add response middleware (1 place)

---

## CellophoneMail-Specific Test Coverage Gaps

From test distribution analysis (2025-10-12-test-distribution-workflow-analysis.md):

### Critical Untested Modules

**1. Middleware - 0 tests (CRITICAL SECURITY GAP)**:
- `middleware/jwt_auth.py` - **0 tests**
  - JWT token extraction from headers vs cookies
  - Token verification logic
  - User attachment to request
  - Guard functions

**Why Critical**: This is the **authentication gate** for the entire application. If compromised, attackers can bypass all security.

**2. Routes - Under-tested**:
- `routes/billing.py` - **0 tests** (financial risk)
- `routes/webhooks.py` - Partial coverage (missing controller tests)
- `routes/auth.py` - Missing login, logout, refresh endpoints

**Why Important**: Routes are the **public API surface**. Untested routes = unverified contracts with clients.

**3. Services - Mixed Coverage**:
- ✅ `services/auth_service.py` - **21 tests** (excellent)
- ✅ `services/stripe_service.py` - **9 tests** (good)
- ❌ `services/email_routing_service.py` - **0 tests** (critical junction)
- ❌ `services/user_service.py` - **0 tests** (core operations)

**Why Important**: Services contain **business logic**. Bugs here cause data corruption, security issues, financial errors.

---

## Testing Strategy by Layer

### Services (Easiest - Do This First)

**Example** - Testing `services/auth_service.py`:
```python
# tests/test_auth_service.py
def test_hash_password():
    password = "SecurePass123"
    hashed = hash_password(password)

    # Verify hashing worked
    assert len(hashed) > 0
    assert hashed != password  # Not plain text
    assert verify_password(password, hashed) == True
    assert verify_password("WrongPass", hashed) == False

async def test_validate_email_unique():
    # Test with existing email
    exists = await validate_email_unique("existing@example.com")
    assert exists == False

    # Test with new email
    unique = await validate_email_unique("new@example.com")
    assert unique == True
```

### Routes (Moderate - Do This Second)

**Example** - Testing `routes/billing.py`:
```python
# tests/test_billing_routes.py
async def test_create_checkout_success():
    async with AsyncTestClient(app=app) as client:
        # Create authenticated request
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = await client.post(
            "/billing/create-checkout",
            json={"price_id": "price_123"},
            headers=headers
        )

        assert response.status_code == 200
        assert "checkout_url" in response.json()
```

### Middleware (Hardest - Do This Last)

**Example** - Testing `middleware/jwt_auth.py`:
```python
# tests/test_jwt_middleware.py
async def test_authenticate_request_with_valid_token():
    # Create mock ASGI connection
    connection = create_mock_connection(
        headers={"Authorization": "Bearer valid_token_here"}
    )

    middleware = JWTAuthenticationMiddleware()
    result = await middleware.authenticate_request(connection)

    assert result.user is not None
    assert result.user.id == "expected_user_id"
    assert result.user.email == "user@example.com"

async def test_authenticate_request_with_cookie():
    connection = create_mock_connection(
        cookies={"access_token": "valid_token_here"}
    )

    middleware = JWTAuthenticationMiddleware()
    result = await middleware.authenticate_request(connection)

    assert result.user is not None

async def test_authenticate_request_no_token():
    connection = create_mock_connection()

    middleware = JWTAuthenticationMiddleware()
    result = await middleware.authenticate_request(connection)

    assert result.user is None  # Anonymous request
```

---

## Visual Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    HTTP REQUEST                          │
│              (User clicks "Login")                       │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  MIDDLEWARE LAYER (Cross-Cutting Concerns)               │
│  ┌────────────────────────────────────────────────────┐  │
│  │  JWTAuthenticationMiddleware                       │  │
│  │  - Runs on EVERY request                           │  │
│  │  - Extracts JWT from header OR cookie              │  │
│  │  - Verifies token signature & expiry               │  │
│  │  - Creates JWTUser object                          │  │
│  │  - Sets request.user = JWTUser(...)                │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Other middleware: CORS, Logging, Rate Limiting          │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  ROUTES LAYER (HTTP Interface / Controllers)             │
│  ┌────────────────────────────────────────────────────┐  │
│  │  POST /auth/login                                  │  │
│  │  - Parse request body (UserLogin model)           │  │
│  │  - Validate input (Pydantic)                      │  │
│  │  - Call: user = await User.objects().where(...)   │  │
│  │  - Call: verify_password(password, user.hash)     │  │
│  │  - Call: create_dual_auth_response(user)          │  │
│  │  - Return: Response(status_code=200, ...)         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Thin controllers - orchestrate services                 │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  SERVICES LAYER (Business Logic)                         │
│  ┌────────────────────────────────────────────────────┐  │
│  │  auth_service.verify_password()                    │  │
│  │  - Input: (plain_password, hash)                   │  │
│  │  - Logic: bcrypt.checkpw(...)                      │  │
│  │  - Output: bool (True/False)                       │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  jwt_service.create_access_token()                 │  │
│  │  - Input: (user_id, email, role)                   │  │
│  │  - Logic: jwt.encode(payload, SECRET_KEY, HS256)   │  │
│  │  - Output: JWT token string                        │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Reusable, framework-agnostic business logic             │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  DATABASE / MODELS                                       │
│  - User.objects().where(User.email == ...).first()      │
│  - Piccolo ORM queries                                   │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                    HTTP RESPONSE                         │
│  {                                                       │
│    "access_token": "eyJ...",                             │
│    "user": {"id": "123", "email": "user@example.com"}   │
│  }                                                       │
│  Set-Cookie: access_token=eyJ...; HttpOnly; Secure      │
└──────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Routes** = Thin HTTP controllers that orchestrate services
2. **Services** = Reusable business logic (easiest to test)
3. **Middleware** = Cross-cutting concerns that run on every request

4. **Testing Priority**:
   - ✅ Services first (easy, high value)
   - ⚠️ Routes second (moderate difficulty)
   - ❌ Middleware third (hard but critical for security)

5. **Current Gaps** (from test analysis):
   - Middleware: **0 tests** (CRITICAL)
   - Routes: Under-tested (**billing.py: 0 tests**)
   - Services: Mixed (**email_routing_service.py: 0 tests**)

6. **Architectural Benefits**:
   - Separation of concerns
   - Reusability (services called from multiple routes)
   - Testability (test each layer independently)
   - Maintainability (change one layer without affecting others)

---

## Related Documents

- `thoughts/shared/research/2025-10-12-test-distribution-workflow-analysis.md` - Test coverage by workflow
- `thoughts/shared/research/2025-10-12-test-coverage-ci-cd-infrastructure.md` - Overall test infrastructure
- `thoughts/shared/plans/2025-10-12-unit-testing-infrastructure-enhancement.md` - Testing improvement plan

## Code References

- `src/cellophanemail/routes/auth.py` - Authentication routes
- `src/cellophanemail/services/auth_service.py` - Authentication services
- `src/cellophanemail/middleware/jwt_auth.py` - JWT middleware
- `src/cellophanemail/services/email_routing_service.py` - Email routing service
- `tests/test_auth_service.py` - Service layer tests example
