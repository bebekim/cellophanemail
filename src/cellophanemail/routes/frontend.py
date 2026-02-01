"""Frontend page controllers for CellophoneMail."""

from litestar import get
from litestar.controller import Controller
from litestar.response import Template
from litestar.request import Request
from ..config.pricing import (
    get_plan_details,
    get_addon_pack_details,
    TRIAL_PERIOD_DAYS
)


class FrontendController(Controller):
    """Frontend page rendering controllers."""

    path = "/"

    @get("/auth/register")
    async def register_page(self, request: Request) -> Template:
        """Render the user registration form."""
        return Template(
            template_name="auth/register.html",
            context={
                "page_title": "Sign Up - CellophoneMail",
                "meta_description": "Create your CellophoneMail account for AI-powered email protection",
                "request": request,
            }
        )

    @get("/auth/login")
    async def login_page(self, request: Request) -> Template:
        """Render the user login form."""
        return Template(
            template_name="auth/login.html",
            context={
                "page_title": "Log In - CellophoneMail",
                "meta_description": "Sign in to your CellophoneMail account",
                "request": request,
            }
        )

    @get("/auth/signup-success")
    async def signup_success_page(self, request: Request) -> Template:
        """Render the signup success page."""
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

    @get("/")
    async def landing_page(self) -> Template:
        """Render the landing page."""
        return Template(
            template_name="landing.html",
            context={
                "page_title": "CellophoneMail - AI-Powered Email Protection",
                "meta_description": "Protect your inbox from toxic emails with AI-powered Four Horsemen analysis. Get your shield email address today.",
                "trial_days": TRIAL_PERIOD_DAYS
            }
        )
    
    @get("/terms")
    async def terms_page(self) -> Template:
        """Render the terms of service page."""
        return Template(
            template_name="legal/terms.html",
            context={
                "page_title": "Terms of Service - CellophoneMail",
                "meta_description": "CellophoneMail terms of service and user agreement"
            }
        )
    
    @get("/privacy")
    async def privacy_page(self) -> Template:
        """Render the privacy policy page."""
        return Template(
            template_name="legal/privacy.html",
            context={
                "page_title": "Privacy Policy - CellophoneMail", 
                "meta_description": "CellophoneMail privacy policy and data protection"
            }
        )

    @get("/pricing")
    async def pricing_page(self) -> Template:
        """Render the pricing page."""
        # Get plan details from pricing config
        starter_plan = get_plan_details("starter")
        professional_plan = get_plan_details("professional") 
        unlimited_plan = get_plan_details("unlimited")
        addon_pack = get_addon_pack_details()
        
        return Template(
            template_name="pricing.html",
            context={
                "page_title": "Pricing - CellophoneMail",
                "meta_description": "Choose the perfect CellophoneMail plan for your email protection needs. Starting at $5/month with 30-day free trial.",
                "plans": [
                    {
                        "id": "starter",
                        "name": "Starter",
                        "price": starter_plan["price"],
                        "period": "month",
                        "email_limit": starter_plan["emails"],
                        "description": starter_plan["description"],
                        "features": [
                            f"{starter_plan['emails']} emails per month",
                            "1 shield email address",
                            "Four Horsemen AI analysis",
                            "Basic dashboard",
                            "Email support"
                        ],
                        "cta": "Start Free Trial",
                        "popular": False
                    },
                    {
                        "id": "professional", 
                        "name": "Professional",
                        "price": professional_plan["price"],
                        "period": "month",
                        "email_limit": professional_plan["emails"],
                        "description": professional_plan["description"],
                        "features": [
                            f"{professional_plan['emails']} emails per month",
                            "3 shield email addresses",
                            "Advanced Four Horsemen analytics",
                            "Watch list management",
                            "Priority support",
                            "Custom reporting"
                        ],
                        "cta": "Start Free Trial",
                        "popular": True
                    },
                    {
                        "id": "unlimited",
                        "name": "Unlimited", 
                        "price": unlimited_plan["price"],
                        "period": "month",
                        "email_limit": None,
                        "description": unlimited_plan["description"],
                        "features": [
                            "Unlimited emails",
                            "Unlimited shield addresses",
                            "Advanced Four Horsemen analytics",
                            "Watch list management", 
                            "Priority support",
                            "Custom domains",
                            "API access"
                        ],
                        "cta": "Start Free Trial",
                        "popular": False
                    }
                ],
                "addon_pack": {
                    "price": addon_pack["price"],
                    "emails": addon_pack["emails"],
                    "description": addon_pack["description"]
                },
                "trial_days": TRIAL_PERIOD_DAYS
            }
        )


# Export router for app registration
router = FrontendController