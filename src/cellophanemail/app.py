"""CellophoneMail - Litestar Application Factory with Plugin Architecture."""

import asyncio
import logging
from contextlib import asynccontextmanager
from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.config.compression import CompressionConfig
from litestar.config.csrf import CSRFConfig
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.di import Provide
from litestar.plugins.pydantic import PydanticPlugin
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from pathlib import Path

from .config.settings import get_settings
from .routes import health, webhooks, auth, frontend, billing, stripe_webhooks
from .plugins.manager import PluginManager
from .middleware.jwt_auth import JWTAuthenticationMiddleware
from .providers.postmark.webhook import PostmarkWebhookHandler
from .providers.gmail.webhook import GmailWebhookHandler
from .features.email_protection.memory_manager_singleton import get_memory_manager
from .features.email_protection.background_cleanup import BackgroundCleanupService

logger = logging.getLogger(__name__)

# Global cleanup service for memory management
_cleanup_service: BackgroundCleanupService = None


def validate_configuration(settings) -> None:
    """Validate configuration for security issues at startup."""
    errors = []

    # Check for required production settings
    if settings.is_production:
        if not settings.encryption_key:
            errors.append("ENCRYPTION_KEY is required in production mode")
        if not settings.anthropic_api_key and settings.ai_provider == "anthropic":
            errors.append("ANTHROPIC_API_KEY is required for AI features")
        if settings.email_delivery_method == "postmark" and not settings.postmark_api_token:
            errors.append("POSTMARK_API_TOKEN is required for Postmark email delivery")
        if settings.email_delivery_method == "smtp" and not settings.email_password:
            errors.append("EMAIL_PASSWORD is required for SMTP email delivery")

    # Check for development-specific issues
    if not settings.is_production:
        if settings.secret_key == "dev-secret-key-change-in-production":
            errors.append("Default SECRET_KEY detected - this is a security risk even in development")

    # Check for database URL issues (always validate)
    if "postgres:password@" in settings.database_url.lower():
        errors.append("DATABASE_URL contains default password 'password' - use a secure password")

    if errors:
        error_message = f"Configuration validation failed:\n  - " + "\n  - ".join(errors)
        logger.error(error_message)
        raise ValueError(error_message)


@asynccontextmanager
async def lifespan(app: Litestar):
    """
    Lifespan manager for CellophoneMail application.
    Handles startup and shutdown of background services.
    """
    global _cleanup_service
    
    # Startup: Initialize and start background cleanup service
    logger.info("Starting CellophoneMail background services...")
    
    # Get shared memory manager (same instance used by privacy orchestrator)
    memory_manager = get_memory_manager()
    
    # Initialize cleanup service with 1-minute grace period
    _cleanup_service = BackgroundCleanupService(
        memory_manager=memory_manager,
        grace_period_minutes=1
    )
    
    # Start scheduled cleanup every 60 seconds
    await _cleanup_service.start_scheduled_cleanup(interval_seconds=60)
    
    logger.info("Background cleanup service started (60s intervals, 1min grace period)")
    
    yield  # Application runs here
    
    # Shutdown: Clean up background services
    logger.info("Shutting down CellophoneMail background services...")
    
    if _cleanup_service:
        await _cleanup_service.stop_scheduled_cleanup()
        logger.info("Background cleanup service stopped")


@get("/favicon.ico")
async def favicon() -> dict:
    """Return empty response for favicon requests."""
    return {}


def create_app() -> Litestar:
    """Create CellophoneMail Litestar application with SaaS features."""
    settings = get_settings()

    # Validate configuration before starting application
    try:
        validate_configuration(settings)
        logger.info("Configuration validation passed")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    # Plugin system initialization
    plugin_manager = PluginManager()
    
    # SaaS configuration
    cors_config = CORSConfig(
        allow_origins=settings.cors_allowed_origins_list,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    
    # CSRF protection for state-changing operations (important for SaaS)
    # Disable CSRF in testing mode only
    csrf_config = None
    if not settings.testing:
        csrf_config = CSRFConfig(
            secret=settings.secret_key,
            cookie_name="cellophane_csrf",
            header_name="X-CSRF-Token",
            exclude=["/webhooks/*", "/health/*", "/providers/*", "/billing/create-checkout"],  # Webhooks and providers need to work without CSRF
            safe_methods=["GET", "HEAD", "OPTIONS"],
        )
    
    compression_config = CompressionConfig(
        backend="gzip",
        minimum_size=1024,
    )
    
    rate_limit_config = RateLimitConfig(
        rate_limit=("minute", 100),  # 100 requests per minute
        exclude=["health", "webhooks"],  # Don't rate limit these
    )
    
    openapi_config = OpenAPIConfig(
        title="CellophoneMail API",
        version="1.0.0",
        description="AI-powered email protection SaaS with Four Horsemen analysis",
        path="/docs",
    )
    
    # Template configuration for Jinja2
    template_config = TemplateConfig(
        directory=Path(__file__).parent / "templates",
        engine=JinjaTemplateEngine,
    )
    
    # Create Litestar app with lifespan management
    app = Litestar(
        route_handlers=[
            favicon,
            frontend.router,  # Frontend pages (landing, pricing, etc.)
            health.router,
            webhooks.router,  # Legacy webhooks (will migrate later)
            auth.router,
            billing.BillingController,  # Stripe billing and checkout
            stripe_webhooks.StripeWebhookHandler,  # Stripe webhook events
            PostmarkWebhookHandler,  # New provider-based webhook
            GmailWebhookHandler,  # Gmail provider webhook
        ],
        cors_config=cors_config,
        csrf_config=csrf_config,
        compression_config=compression_config,
        openapi_config=openapi_config,
        template_config=template_config,
        lifespan=[lifespan],  # Background services lifecycle management
        middleware=[
            JWTAuthenticationMiddleware,  # JWT authentication middleware
        ],
        dependencies={
            "plugin_manager": Provide(lambda: plugin_manager, sync_to_thread=False),
            "settings": Provide(lambda: settings, sync_to_thread=False),
        },
        debug=settings.debug,
        pdb_on_exception=settings.debug if not settings.testing else False,  # Disable pdb during tests
        plugins=[PydanticPlugin()],
    )
    
    return app


# Entry point for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "cellophanemail.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else 4,
    )