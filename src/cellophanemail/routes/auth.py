"""Authentication and user management endpoints."""

from litestar import post, get, Response
from litestar.controller import Controller
from litestar.response import Template, Redirect
from litestar.security.jwt import JWTAuth
from litestar.status_codes import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_302_FOUND
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Dict, Any, Optional
import secrets
import urllib.parse
from cellophanemail.services.auth_service import (
    validate_email_unique,
    create_user,
    verify_password,
    handle_google_oauth_callback
)
from cellophanemail.config.settings import get_settings


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
            
            # TODO: Generate JWT token for the user
            # TODO: Set session cookie
            
            return Response(
                content={
                    "status": "authenticated",
                    "user_id": str(user.id),
                    "email": user.email,
                    "shield_address": f"{user.username}@cellophanemail.com",
                    "oauth_provider": user.oauth_provider,
                    "message": "Successfully authenticated with Google",
                    "redirect_url": "/dashboard"
                },
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
    ) -> Dict[str, Any]:
        """Authenticate user login."""
        
        # TODO: Validate credentials
        # TODO: Generate JWT token
        # TODO: Update last login
        
        return {
            "status": "authenticated",
            "access_token": "temp_token",
            "token_type": "bearer",
            "expires_in": 3600
        }
    
    @get("/profile")
    async def get_user_profile(self) -> Dict[str, Any]:
        """Get authenticated user profile."""
        
        # TODO: Extract user from JWT
        # TODO: Return user profile data
        
        return {
            "user_id": "temp_id", 
            "email": "user@example.com",
            "plan": "basic",
            "cellophane_address": "user123@cellophanemail.com",
            "usage": {
                "emails_processed": 42,
                "monthly_limit": 1000
            }
        }
    
    @post("/logout")
    async def logout_user(self) -> Dict[str, str]:
        """Logout user (invalidate token)."""
        
        # TODO: Add token to blacklist
        
        return {"status": "logged_out"}


# Export router for app registration
router = AuthController