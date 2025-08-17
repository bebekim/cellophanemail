"""JWT authentication middleware for Litestar."""

from typing import Optional, Dict, Any
from litestar import Request, Response
from litestar.connection import ASGIConnection
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.exceptions import NotAuthorizedException
from cellophanemail.services.jwt_service import verify_token, TokenType, JWTError, TokenPayload
from cellophanemail.models.user import User


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
        """Authenticate request using JWT token.
        
        Args:
            connection: ASGI connection
            
        Returns:
            AuthenticationResult with user and auth info
        """
        # Extract token from Authorization header
        auth_header = connection.headers.get("Authorization", "")
        token = None
        
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        else:
            # Try to get token from cookies as fallback
            token = connection.cookies.get("access_token")
        
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


def jwt_auth_required(connection: ASGIConnection) -> JWTUser:
    """Guard function to require JWT authentication.
    
    Args:
        connection: ASGI connection
        
    Returns:
        Authenticated user
        
    Raises:
        NotAuthorizedException: If user is not authenticated
    """
    user = connection.user
    
    if not user or not isinstance(user, JWTUser):
        raise NotAuthorizedException("Authentication required")
    
    return user


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
        role=user.role or "user"
    )
    
    response_data = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 900,  # 15 minutes
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role or "user",
            "is_verified": user.is_verified
        }
    }
    
    if include_refresh:
        refresh_token = create_refresh_token(user_id=str(user.id))
        response_data["refresh_token"] = refresh_token
    
    return response_data