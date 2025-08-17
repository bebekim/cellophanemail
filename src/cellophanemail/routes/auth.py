"""Authentication and user management endpoints."""

from litestar import post, get, Response, Request
from litestar.controller import Controller
from litestar.response import Template, Redirect
from litestar.security.jwt import JWTAuth
from litestar.status_codes import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_302_FOUND
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import secrets
import urllib.parse
from cellophanemail.services.auth_service import (
    validate_email_unique,
    create_user,
    verify_password,
    handle_google_oauth_callback
)
from cellophanemail.config.settings import get_settings
from cellophanemail.middleware.jwt_auth import jwt_auth_required


class UserRegistration(BaseModel):
    """User registration payload."""
    
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum requirements."""
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
    """User login payload."""
    
    email: EmailStr
    password: str


class AuthController(Controller):
    """Authentication and user management."""
    
    path = "/auth"
    
    @get("/register")
    async def register_form(self) -> Template:
        """Render the user registration form."""
        return Template(
            template_name="auth/register.html",
            context={
                "page_title": "Sign Up - CellophoneMail",
                "meta_description": "Create your CellophoneMail account for AI-powered email protection",
            }
        )
    
    @get("/login") 
    async def login_form(self) -> Template:
        """Render the user login form."""
        return Template(
            template_name="auth/login.html",
            context={
                "page_title": "Log In - CellophoneMail", 
                "meta_description": "Sign in to your CellophoneMail account",
            }
        )
    
    @get("/oauth/google")
    async def google_oauth_redirect(self) -> Redirect:
        """Redirect to Google OAuth authorization URL."""
        settings = get_settings()
        
        if not settings.google_client_id:
            # For development/testing, redirect to callback with error
            return Redirect(
                path="/auth/oauth/google/callback?error=missing_client_id",
                status_code=HTTP_302_FOUND
            )
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        # TODO: Store state in session/cache for verification
        
        # Build Google OAuth URL
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri or "http://localhost:8000/auth/oauth/google/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        return Redirect(path=auth_url, status_code=HTTP_302_FOUND)
    
    @get("/oauth/google/callback")
    async def google_oauth_callback(
        self,
        code: str | None = None,
        oauth_state: str | None = None,
        error: str | None = None
    ) -> Response[Dict[str, Any]]:
        """Handle Google OAuth callback."""
        
        # Handle OAuth errors
        if error:
            return Response(
                content={
                    "error": "oauth_error",
                    "message": f"Google OAuth error: {error}",
                    "redirect_url": "/auth/login"
                },
                status_code=HTTP_400_BAD_REQUEST
            )
        
        if not code:
            return Response(
                content={
                    "error": "missing_code",
                    "message": "Missing authorization code from Google",
                    "redirect_url": "/auth/login"
                },
                status_code=HTTP_400_BAD_REQUEST
            )
        
        # TODO: Verify oauth_state parameter for CSRF protection
        
        try:
            # Handle OAuth callback using the auth service
            user = await handle_google_oauth_callback(code)
            
            # Create JWT tokens
            from cellophanemail.middleware.jwt_auth import create_auth_response
            auth_response = await create_auth_response(user)
            
            # Add additional OAuth-specific info
            auth_response.update({
                "oauth_provider": user.oauth_provider,
                "message": "Successfully authenticated with Google",
                "redirect_url": "/dashboard"
            })
            
            return Response(
                content=auth_response,
                status_code=HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                content={
                    "error": "oauth_callback_failed",
                    "message": f"Failed to process Google OAuth callback: {str(e)}",
                    "redirect_url": "/auth/login"
                },
                status_code=HTTP_400_BAD_REQUEST
            )
    
    @post("/register", status_code=HTTP_201_CREATED)
    async def register_user(
        self,
        data: UserRegistration
    ) -> Response[Dict[str, Any]]:
        """Register new user account."""
        
        # Validate email uniqueness
        is_unique = await validate_email_unique(data.email)
        if not is_unique:
            return Response(
                content={
                    "error": "Email already registered",
                    "field": "email"
                },
                status_code=HTTP_400_BAD_REQUEST
            )
        
        # Create user with hashed password and shield address
        try:
            user = await create_user(
                email=data.email,
                password=data.password,
                first_name=data.first_name,
                last_name=data.last_name
            )
            
            # TODO: Send welcome/verification email via Postmark
            # TODO: Generate JWT token for auto-login
            # TODO: Create Stripe checkout session for trial
            
            return Response(
                content={
                    "status": "registered",
                    "user_id": str(user.id),
                    "email": user.email,
                    "shield_address": f"{user.username}@cellophanemail.com",
                    "email_verified": user.is_verified,
                    "verification_token": user.verification_token,
                    "message": "Registration successful. Please check your email to verify your account."
                },
                status_code=HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                content={
                    "error": "Registration failed",
                    "message": str(e)
                },
                status_code=HTTP_400_BAD_REQUEST
            )
    
    @post("/login")
    async def login_user(
        self,
        data: UserLogin  
    ) -> Response[Dict[str, Any]]:
        """Authenticate user login."""
        from cellophanemail.models.user import User
        from cellophanemail.middleware.jwt_auth import create_auth_response
        
        # Find user by email
        user = await User.objects().where(
            User.email == data.email
        ).first()
        
        if not user:
            return Response(
                content={
                    "error": "Invalid credentials",
                    "message": "Email or password is incorrect"
                },
                status_code=HTTP_400_BAD_REQUEST
            )
        
        # Verify password
        is_valid = await verify_password(data.password, user.hashed_password)
        
        if not is_valid:
            return Response(
                content={
                    "error": "Invalid credentials",
                    "message": "Email or password is incorrect"
                },
                status_code=HTTP_400_BAD_REQUEST
            )
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await user.save()
        
        # Create JWT tokens
        auth_response = await create_auth_response(user)
        
        return Response(
            content=auth_response,
            status_code=200
        )
    
    @get("/profile", guards=[jwt_auth_required])
    async def get_user_profile(self, request: Request) -> Dict[str, Any]:
        """Get authenticated user profile."""
        from cellophanemail.models.user import User
        
        # Get authenticated user from request
        jwt_user = request.user
        
        # Fetch full user data from database
        user = await User.objects().where(
            User.id == int(jwt_user.id)
        ).first()
        
        if not user:
            return Response(
                content={"error": "User not found"},
                status_code=404
            )
        
        return {
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role or "user",
            "is_verified": user.is_verified,
            "shield_address": f"{user.username}@cellophanemail.com",
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "usage": {
                "emails_processed": 0,  # TODO: Implement usage tracking
                "monthly_limit": 1000
            }
        }
    
    @post("/logout", guards=[jwt_auth_required])
    async def logout_user(self, request: Request) -> Dict[str, str]:
        """Logout user (invalidate token)."""
        from cellophanemail.services.jwt_service import blacklist_token, decode_token
        
        # Get token from request
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            
            # Decode token to get JTI
            try:
                payload = decode_token(token)
                jti = payload.get("jti")
                
                if jti:
                    # Add token to blacklist
                    blacklist_token(jti)
            except Exception:
                pass  # Token already invalid, no need to blacklist
        
        return {"status": "logged_out", "message": "Successfully logged out"}
    
    @post("/refresh")
    async def refresh_token(
        self,
        data: Dict[str, str]
    ) -> Response[Dict[str, Any]]:
        """Refresh access token using refresh token."""
        from cellophanemail.services.jwt_service import refresh_access_token, JWTError
        
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            return Response(
                content={
                    "error": "Missing refresh token",
                    "message": "Refresh token is required"
                },
                status_code=HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate new access token
            new_access_token = await refresh_access_token(refresh_token)
            
            return Response(
                content={
                    "access_token": new_access_token,
                    "token_type": "Bearer",
                    "expires_in": 900  # 15 minutes
                },
                status_code=200
            )
            
        except JWTError as e:
            return Response(
                content={
                    "error": "Invalid refresh token",
                    "message": str(e)
                },
                status_code=HTTP_400_BAD_REQUEST
            )


# Export router for app registration
router = AuthController