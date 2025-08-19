"""JWT authentication middleware for Litestar."""

from typing import Optional, Dict, Any
from litestar import Request, Response
from litestar.connection import ASGIConnection
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.exceptions import NotAuthorizedException
from ..services.jwt_service import verify_token, TokenType, JWTError, TokenPayload
from ..models.user import User


class JWTUser:
    """Authenticated user from JWT token."""
    
    def __init__(self, user_id: str, email: str, role: str = "user"):
        self.id = user_id
        self.email = email
        self.role = role
        self.is_authenticated = True
    
    @classmethod
    async def from_token_payload(cls, payload: TokenPayload) -> "JWTUser":
        """Create JWTUser from token payload.
        
        Args:
            payload: Decoded JWT token payload
            
        Returns:
            JWTUser instance
        """
        return cls(
            user_id=payload.sub,
            email=payload.email or "",
            role=payload.role or "user"
        )


class JWTAuthenticationMiddleware(AbstractAuthenticationMiddleware):
    """JWT authentication middleware."""
    
    async def authenticate_request(
        self,
        connection: ASGIConnection
    ) -> AuthenticationResult:
        """Authenticate request using JWT token with multiple source priority.
        
        Token extraction priority:
        1. Authorization header (for API calls)
        2. httpOnly access_token cookie (for browser navigation)
        
        Args:
            connection: ASGI connection
            
        Returns:
            AuthenticationResult with user and auth info
        """
        token = self._extract_token_with_priority(connection)
        
        if not token:
            # Return empty auth result (no user authenticated)
            return AuthenticationResult(user=None, auth=None)
        
        try:
            # Verify token
            payload = await verify_token(token, TokenType.ACCESS)
            
            # Create user object
            user = await JWTUser.from_token_payload(payload)
            
            # Return authentication result
            return AuthenticationResult(user=user, auth=token)
            
        except JWTError:
            # Invalid token, return empty auth result
            return AuthenticationResult(user=None, auth=None)
    
    def _extract_token_with_priority(self, connection: ASGIConnection) -> Optional[str]:
        """Extract JWT token from multiple sources with priority order.
        
        Priority:
        1. Authorization header (API calls)
        2. httpOnly cookie (browser navigation)
        
        Args:
            connection: ASGI connection
            
        Returns:
            JWT token string or None
        """
        # Priority 1: Authorization header
        auth_header = connection.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header.replace("Bearer ", "")
        
        # Priority 2: httpOnly cookie
        cookie_token = connection.cookies.get("access_token")
        if cookie_token:
            return cookie_token
        
        # No token found
        return None


def jwt_auth_required(connection: ASGIConnection, route_handler) -> None:
    """Guard function to require JWT authentication.
    
    Args:
        connection: ASGI connection
        route_handler: The route handler being protected
        
    Raises:
        NotAuthorizedException: If user is not authenticated
    """
    user = connection.user
    
    if not user or not isinstance(user, JWTUser):
        raise NotAuthorizedException("Authentication required")


def jwt_auth_optional(connection: ASGIConnection) -> Optional[JWTUser]:
    """Guard function for optional JWT authentication.
    
    Args:
        connection: ASGI connection
        
    Returns:
        Authenticated user or None
    """
    user = connection.user
    
    if user and isinstance(user, JWTUser):
        return user
    
    return None


async def create_auth_response(
    user: User,
    include_refresh: bool = True
) -> Dict[str, Any]:
    """Create authentication response with JWT tokens.
    
    Args:
        user: User model instance
        include_refresh: Whether to include refresh token
        
    Returns:
        Dictionary with tokens and user info
    """
    from cellophanemail.services.jwt_service import create_access_token, create_refresh_token
    
    # Create tokens
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role="user"  # Default role since User model doesn't have role field
    )
    
    response_data = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 900,  # 15 minutes
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": "user",  # Default role since User model doesn't have role field
            "is_verified": user.is_verified
        }
    }
    
    if include_refresh:
        refresh_token = create_refresh_token(user_id=str(user.id))
        response_data["refresh_token"] = refresh_token
    
    return response_data


async def create_dual_auth_response(
    user: User,
    response: Response,
    include_refresh: bool = True
) -> Response:
    """Create authentication response with both cookies and tokens for hybrid auth.
    
    Args:
        user: User model instance
        response: Response object to set cookies on
        include_refresh: Whether to include refresh token
        
    Returns:
        Response with secure cookies set and JSON token data
    """
    from cellophanemail.services.jwt_service import create_access_token, create_refresh_token
    from cellophanemail.config.settings import get_settings
    
    settings = get_settings()
    
    # Create tokens
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role="user"
    )
    
    # Set secure httpOnly cookie for browser navigation
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=900,  # 15 minutes (same as token expiry)
        httponly=True,  # Prevent XSS
        secure=not settings.debug,  # HTTPS only in production
        samesite="lax"  # CSRF protection while allowing normal navigation
    )
    
    # Prepare response data for localStorage (API calls)
    response_data = {
        "access_token": access_token,
        "token_type": "Bearer", 
        "expires_in": 900,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": "user",
            "is_verified": user.is_verified
        }
    }
    
    if include_refresh:
        refresh_token = create_refresh_token(user_id=str(user.id))
        response_data["refresh_token"] = refresh_token
        
        # Also set refresh token cookie with longer expiry
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=not settings.debug,
            samesite="lax"
        )
    
    # Set the response content
    response.content = response_data
    return response