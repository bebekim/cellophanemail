"""Authentication and user management endpoints."""

from litestar import post, get, Response, Request
from litestar.controller import Controller
from litestar.response import Template, Redirect
from litestar.security.jwt import JWTAuth
from litestar.status_codes import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_302_FOUND
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from ..services.auth_service import (
    validate_email_unique,
    create_user,
    verify_password
)
from ..services.stripe_service import StripeService
from ..config.settings import get_settings
from ..middleware.jwt_auth import jwt_auth_required


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
    async def register_form(self, request: Request) -> Template:
        """Render the user registration form."""
        return Template(
            template_name="auth/register.html",
            context={
                "page_title": "Sign Up - CellophoneMail",
                "meta_description": "Create your CellophoneMail account for AI-powered email protection",
                "request": request,
            }
        )
    
    @get("/login") 
    async def login_form(self, request: Request) -> Template:
        """Render the user login form."""
        return Template(
            template_name="auth/login.html",
            context={
                "page_title": "Log In - CellophoneMail", 
                "meta_description": "Sign in to your CellophoneMail account",
                "request": request,
            }
        )
    
    @get("/signup-success")
    async def signup_success(self, request: Request) -> Template:
        """Render the signup success page."""
        # Get user details from query parameters (passed from registration)
        user_email = request.query_params.get("email", "")
        shield_address = request.query_params.get("shield_address", "")
        email_verified = request.query_params.get("verified", "false").lower() == "true"
        
        return Template(
            template_name="auth/signup_success.html",
            context={
                "page_title": "Welcome to CellophoneMail - Registration Successful",
                "meta_description": "Your CellophoneMail account has been created successfully",
                "user_email": user_email,
                "shield_address": shield_address,
                "email_verified": email_verified,
                "request": request,
            }
        )
    
    @get("/dashboard", guards=[jwt_auth_required])
    async def dashboard(self, request: Request) -> Template:
        """Render the user dashboard."""
        from cellophanemail.models.user import User
        
        # Get authenticated user from request
        jwt_user = request.user
        
        # Fetch full user data from database
        user = await User.objects().where(
            User.id == jwt_user.id
        ).first()
        
        if not user:
            return Template(
                template_name="errors/404.html",
                context={"page_title": "User Not Found"}
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
                "created_at": "2025-01-15"
            },
            {
                "id": 2,
                "designation": "Service Notifications", 
                "email_address": "notifications@service.com",
                "emails_received": 23,
                "emails_filtered": 8,
                "created_at": "2025-01-10"
            }
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

            # Create Stripe customer
            stripe_service = StripeService()
            customer = await stripe_service.create_customer(
                user_id=str(user.id),
                email=user.email,
                name=f"{user.first_name or ''} {user.last_name or ''}".strip()
            )

            # Store customer ID
            user.stripe_customer_id = customer.id
            await user.save()

            # TODO: Send welcome/verification email via Postmark
            # TODO: Generate JWT token for auto-login

            return Response(
                content={
                    "status": "registered",
                    "user_id": str(user.id),
                    "email": user.email,
                    "shield_address": f"{user.username}@cellophanemail.com",
                    "stripe_customer_id": customer.id,
                    "email_verified": user.is_verified,
                    "verification_token": user.verification_token,
                    "message": "Registration successful. Use /billing/create-checkout to start your subscription."
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
        """Authenticate user login with hybrid cookie + token strategy."""
        from cellophanemail.models.user import User
        from cellophanemail.middleware.jwt_auth import create_dual_auth_response
        
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
        is_valid = verify_password(data.password, user.hashed_password)
        
        if not is_valid:
            return Response(
                content={
                    "error": "Invalid credentials",
                    "message": "Email or password is incorrect"
                },
                status_code=HTTP_400_BAD_REQUEST
            )
        
        # TODO: Update last login (fix timezone issue first)
        # user.last_login = datetime.now(timezone.utc)
        # await user.save()
        
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
        user = await User.objects().where(
            User.id == jwt_user.id
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
            "role": "user",  # Default role since User model doesn't have role field
            "is_verified": user.is_verified,
            "shield_address": f"{user.username}@cellophanemail.com",
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "usage": {
                "emails_processed": 0,  # TODO: Implement usage tracking
                "monthly_limit": 1000
            }
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
                "message": "Successfully logged out. Please clear localStorage manually."
            },
            status_code=200
        )
        
        # Clear authentication cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        return response
    
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