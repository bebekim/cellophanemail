"""Test factories for creating mock objects."""

from unittest.mock import MagicMock, AsyncMock
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class UserFactory:
    """Factory for creating mock User objects."""

    @staticmethod
    def create_user(
        user_id: str = "user-123",
        email: str = "test@example.com",
        username: str = "test123",
        is_verified: bool = True,
        stripe_customer_id: Optional[str] = None,
        **kwargs
    ) -> MagicMock:
        """Create a mock User object with sensible defaults."""
        user = MagicMock()
        user.id = user_id
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
        user_id: str = "user-123",
        email: str = "test@example.com",
        username: str = "test123",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a user dictionary (for service return values)."""
        return {
            "id": user_id,
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
        customer_id: str = "cus_123",
        email: str = "test@example.com",
        name: str = "Test User",
        **kwargs
    ) -> MagicMock:
        """Create a mock Stripe Customer object."""
        customer = MagicMock()
        customer.id = customer_id
        customer.email = email
        customer.name = name
        customer.metadata = kwargs.get("metadata", {"user_id": "user-123"})
        return customer

    @staticmethod
    def create_checkout_session(
        session_id: str = "cs_test_123",
        url: str = "https://checkout.stripe.com/test",
        **kwargs
    ) -> MagicMock:
        """Create a mock Stripe Checkout Session."""
        session = MagicMock()
        session.id = session_id
        session.url = url
        session.customer = kwargs.get("customer", "cus_123")
        session.mode = kwargs.get("mode", "subscription")
        return session

    @staticmethod
    def create_portal_session(
        session_id: str = "bps_test_123",
        url: str = "https://billing.stripe.com/test",
        **kwargs
    ) -> MagicMock:
        """Create a mock Stripe Portal Session."""
        session = MagicMock()
        session.id = session_id
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
