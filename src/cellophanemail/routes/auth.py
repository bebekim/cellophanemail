"""Authentication and user management endpoints."""

import logging
from litestar import post, get, Response, Request
from litestar.connection import ASGIConnection
from litestar.controller import Controller
from litestar.response import Template
from litestar.status_codes import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_429_TOO_MANY_REQUESTS,
)
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Dict, Any, Optional
from ..services.auth_service import (
    E164_PATTERN,
    validate_email_unique,
    validate_phone_unique,
    find_user_by_identifier,
    create_user,
    verify_password,
)
from ..services.stripe_service import StripeService
from ..middleware.jwt_auth import jwt_auth_required, create_auth_response
from ..features.security.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Auth rate limiter instance
_auth_rate_limiter = RateLimiter()
_auth_rate_limiter.configure_limit("auth:register", requests_per_minute=5)
_auth_rate_limiter.configure_limit("auth:login", requests_per_minute=10)
_auth_rate_limiter.configure_limit("auth:refresh", requests_per_minute=20)


def _get_client_ip(connection: ASGIConnection) -> str:
    """Extract client IP from connection, respecting X-Forwarded-For."""
    forwarded = connection.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = connection.scope.get("client")
    return client[0] if client else "unknown"


def _check_auth_rate_limit(connection: ASGIConnection, endpoint: str) -> None:
    """Check rate limit for an auth endpoint, raise 429 if exceeded."""
    client_ip = _get_client_ip(connection)
    result = _auth_rate_limiter.check_limit(client_ip, endpoint)
    if not result.allowed:
        from litestar.exceptions import HTTPException

        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Retry after {result.retry_after_seconds} seconds.",
            headers={"Retry-After": str(result.retry_after_seconds)},
        )


class UserRegistration(BaseModel):
    """User registration payload — accepts email OR phone_number."""

    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str = Field(
        min_length=8, description="Password must be at least 8 characters"
    )
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None

    @model_validator(mode="after")
    def require_identifier(self):
        if not self.email and not self.phone_number:
            raise ValueError("Either email or phone_number is required")
        return self

    @field_validator("phone_number")
    @classmethod
    def validate_phone_e164(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not E164_PATTERN.match(v):
            raise ValueError("Phone number must be in E.164 format (e.g. +61412345678)")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """User login payload — unified identifier field with legacy email compat."""

    identifier: str
    password: str

    @model_validator(mode="before")
    @classmethod
    def map_legacy_email(cls, values):
        """Support legacy {"email": "..."} payloads by mapping to identifier."""
        if (
            isinstance(values, dict)
            and "email" in values
            and "identifier" not in values
        ):
            values = {**values, "identifier": values.pop("email")}
        return values


class AuthController(Controller):
    """Authentication and user management API endpoints."""

    path = "/api/v1/auth"

    @get("/dashboard", guards=[jwt_auth_required])
    async def dashboard(self, request: Request) -> Template:
        """Render the user dashboard."""
        from cellophanemail.models.user import User

        # Get authenticated user from request
        jwt_user = request.user

        # Fetch full user data from database
        user = await User.objects().where(User.id == jwt_user.id).first()

        if not user:
            return Template(
                template_name="errors/404.html",
                context={"page_title": "User Not Found"},
            )

        # TODO: Fetch protected email addresses from database
        # For now, using mock data
        protected_emails = [
            {
                "id": 1,
                "designation": "Work Alerts",
                "email_address": "alerts@company.com",
                "emails_received": 45,
                "emails_filtered": 12,
                "created_at": "2025-01-15",
            },
            {
                "id": 2,
                "designation": "Service Notifications",
                "email_address": "notifications@service.com",
                "emails_received": 23,
                "emails_filtered": 8,
                "created_at": "2025-01-10",
            },
        ]

        return Template(
            template_name="dashboard.html",
            context={
                "page_title": "Dashboard - CellophoneMail",
                "meta_description": "Manage your email protection settings",
                "user": user,
                "shield_address": f"{user.username}@cellophanemail.com",
                "protected_emails": protected_emails,
                "total_protections": len(protected_emails),
                "request": request,
            },
        )

    @post("/register", status_code=HTTP_201_CREATED)
    async def register_user(
        self, request: Request, data: UserRegistration
    ) -> Response[Dict[str, Any]]:
        """Register new user account."""
        _check_auth_rate_limit(request, "auth:register")

        # Validate uniqueness of whichever identifier was provided
        if data.email:
            is_unique = await validate_email_unique(data.email)
            if not is_unique:
                return Response(
                    content={"error": "Email already registered", "field": "email"},
                    status_code=HTTP_400_BAD_REQUEST,
                )

        if data.phone_number:
            is_unique = await validate_phone_unique(data.phone_number)
            if not is_unique:
                return Response(
                    content={
                        "error": "Phone number already registered",
                        "field": "phone_number",
                    },
                    status_code=HTTP_400_BAD_REQUEST,
                )

        # Create user with hashed password and shield address
        try:
            user = await create_user(
                password=data.password,
                email=data.email,
                phone_number=data.phone_number,
                first_name=data.first_name,
                last_name=data.last_name,
            )

            # Create Stripe customer
            stripe_service = StripeService()
            customer = await stripe_service.create_customer(
                user_id=str(user.id),
                email=user.email or "",
                name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
            )

            # Store customer ID
            user.stripe_customer_id = customer.id
            await user.save()

            # Generate tokens for auto-login after registration
            auth_data = await create_auth_response(user)
            auth_data["shield_address"] = f"{user.username}@cellophanemail.com"
            auth_data["message"] = (
                "Registration successful. Use /billing/create-checkout to start your subscription."
            )

            return Response(
                content=auth_data,
                status_code=HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                content={"error": "Registration failed", "message": str(e)},
                status_code=HTTP_400_BAD_REQUEST,
            )

    @post("/login")
    async def login_user(
        self, request: Request, data: UserLogin
    ) -> Response[Dict[str, Any]]:
        """Authenticate user login with hybrid cookie + token strategy."""
        _check_auth_rate_limit(request, "auth:login")

        from cellophanemail.middleware.jwt_auth import create_dual_auth_response

        # Find user by email or phone
        user = await find_user_by_identifier(data.identifier)

        if not user:
            return Response(
                content={
                    "error": "Invalid credentials",
                    "message": "Email/phone or password is incorrect",
                },
                status_code=HTTP_400_BAD_REQUEST,
            )

        # Verify password
        is_valid = verify_password(data.password, user.hashed_password)

        if not is_valid:
            return Response(
                content={
                    "error": "Invalid credentials",
                    "message": "Email/phone or password is incorrect",
                },
                status_code=HTTP_400_BAD_REQUEST,
            )

        # Create response with both cookies and tokens
        response = Response(content={}, status_code=200)
        response = await create_dual_auth_response(user, response)

        return response

    @get("/profile", guards=[jwt_auth_required])
    async def get_user_profile(self, request: Request) -> Dict[str, Any]:
        """Get authenticated user profile."""
        from cellophanemail.models.user import User

        # Get authenticated user from request
        jwt_user = request.user

        # Fetch full user data from database
        user = await User.objects().where(User.id == jwt_user.id).first()

        if not user:
            return Response(content={"error": "User not found"}, status_code=404)

        return {
            "user_id": str(user.id),
            "email": user.email,
            "phone_number": getattr(user, "phone_number", None),
            "phone_verified": getattr(user, "phone_verified", False),
            "verification_method": getattr(user, "verification_method", None),
            "username": user.username,
            "role": "user",
            "is_verified": user.is_verified,
            "shield_address": f"{user.username}@cellophanemail.com",
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "usage": {
                "emails_processed": 0,
                "monthly_limit": 1000,
            },
        }

    @post("/logout")
    async def logout_user(self, request: Request) -> Response[Dict[str, str]]:
        """Logout user (invalidate tokens and clear cookies)."""
        from cellophanemail.services.jwt_service import blacklist_token, decode_token

        # Get tokens from both sources for blacklisting
        tokens_to_blacklist = []

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            tokens_to_blacklist.append(auth_header.replace("Bearer ", ""))

        # Check cookies
        cookie_access_token = request.cookies.get("access_token")
        if cookie_access_token:
            tokens_to_blacklist.append(cookie_access_token)

        cookie_refresh_token = request.cookies.get("refresh_token")
        if cookie_refresh_token:
            tokens_to_blacklist.append(cookie_refresh_token)

        # Blacklist all found tokens
        for token in tokens_to_blacklist:
            try:
                payload = decode_token(token)
                jti = payload.get("jti")
                if jti:
                    blacklist_token(jti)
            except Exception:
                pass  # Token already invalid, no need to blacklist

        # Create response and clear cookies
        response = Response(
            content={
                "status": "logged_out",
                "message": "Successfully logged out. Please clear localStorage manually.",
            },
            status_code=200,
        )

        # Clear authentication cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response

    @post("/refresh")
    async def refresh_token(
        self, request: Request, data: Dict[str, str]
    ) -> Response[Dict[str, Any]]:
        """Refresh access token using refresh token."""
        _check_auth_rate_limit(request, "auth:refresh")

        from cellophanemail.services.jwt_service import refresh_access_token, JWTError

        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return Response(
                content={
                    "error": "Missing refresh token",
                    "message": "Refresh token is required",
                },
                status_code=HTTP_400_BAD_REQUEST,
            )

        try:
            # Generate new access token
            new_access_token = await refresh_access_token(refresh_token)

            return Response(
                content={
                    "access_token": new_access_token,
                    "token_type": "Bearer",
                    "expires_in": 900,  # 15 minutes
                },
                status_code=200,
            )

        except JWTError as e:
            return Response(
                content={"error": "Invalid refresh token", "message": str(e)},
                status_code=HTTP_400_BAD_REQUEST,
            )


# Export router for app registration
router = AuthController
