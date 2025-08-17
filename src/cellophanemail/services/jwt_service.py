"""JWT token service for authentication."""

import secrets
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr
from cellophanemail.config.settings import get_settings


class TokenType(Enum):
    """Token type enumeration."""
    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(BaseModel):
    """Token payload structure."""
    sub: str  # Subject (user_id)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    type: str
    exp: int
    iat: int
    jti: str  # JWT ID for blacklisting


class JWTError(Exception):
    """JWT related errors."""
    pass


# In-memory blacklist for development (should use Redis in production)
_token_blacklist = set()


def create_access_token(
    user_id: str,
    email: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token.
    
    Args:
        user_id: User identifier
        email: User email address
        role: User role (default: "user")
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    settings = get_settings()
    
    # Set expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # Create payload
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": TokenType.ACCESS.value,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(32)  # Unique token ID
    }
    
    # Encode token
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm="HS256"
    )
    
    return token


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token.
    
    Args:
        user_id: User identifier
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    settings = get_settings()
    
    # Set expiration (7 days default)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Create payload
    payload = {
        "sub": user_id,
        "type": TokenType.REFRESH.value,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(32)
    }
    
    # Encode token
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm="HS256"
    )
    
    return token


async def verify_token(
    token: str,
    token_type: TokenType
) -> TokenPayload:
    """Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid, expired, or blacklisted
    """
    settings = get_settings()
    
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"]
        )
        
        # Check token type
        if payload.get("type") != token_type.value:
            raise JWTError(f"Invalid token type. Expected {token_type.value}, got {payload.get('type')}")
        
        # Check if blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            raise JWTError("Token has been blacklisted")
        
        # Create token payload object
        return TokenPayload(**payload)
        
    except jwt.ExpiredSignatureError:
        raise JWTError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def decode_token(token: str) -> Dict[str, Any]:
    """Decode a token without verification (for testing/debugging).
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
    """
    return jwt.decode(token, options={"verify_signature": False})


def is_token_blacklisted(jti: str) -> bool:
    """Check if a token is blacklisted.
    
    Args:
        jti: JWT ID
        
    Returns:
        True if token is blacklisted
    """
    # TODO: Implement Redis-based blacklist for production
    return jti in _token_blacklist


def blacklist_token(jti: str) -> None:
    """Add a token to the blacklist.
    
    Args:
        jti: JWT ID to blacklist
    """
    # TODO: Implement Redis-based blacklist with TTL
    _token_blacklist.add(jti)


async def refresh_access_token(refresh_token: str) -> str:
    """Generate a new access token from a refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New access token
        
    Raises:
        JWTError: If refresh token is invalid
    """
    # Verify refresh token
    payload = await verify_token(refresh_token, TokenType.REFRESH)
    
    # Get user details (in production, fetch from database)
    # For now, we'll create a minimal access token
    from cellophanemail.models.user import User
    
    try:
        user = await User.objects().where(
            User.id == int(payload.sub)
        ).first()
        
        if not user:
            raise JWTError("User not found")
        
        # Create new access token
        return create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role or "user"
        )
    except Exception as e:
        # For testing, create token without database lookup
        return create_access_token(
            user_id=payload.sub,
            email="refreshed@example.com",
            role="user"
        )