"""Authentication and user management endpoints."""

from litestar import post, get, Response
from litestar.controller import Controller
from litestar.response import Template
from litestar.security.jwt import JWTAuth
from litestar.status_codes import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Dict, Any, Optional
from cellophanemail.services.auth_service import (
    validate_email_unique,
    create_user,
    verify_password
)


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