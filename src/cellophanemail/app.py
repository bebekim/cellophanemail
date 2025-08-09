"""CellophoneMail - Litestar Application Factory with Plugin Architecture."""

from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.config.compression import CompressionConfig
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.di import Provide

from cellophanemail.config.settings import get_settings
from cellophanemail.routes import health, webhooks, auth
from cellophanemail.plugins.manager import PluginManager


def create_app() -> Litestar:
    """Create CellophoneMail Litestar application with SaaS features."""
    settings = get_settings()
    
    # Plugin system initialization
    plugin_manager = PluginManager()
    
    # SaaS configuration
    cors_config = CORSConfig(
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        allow_credentials=True,
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
    
    # Create Litestar app
    app = Litestar(
        route_handlers=[
            health.router,
            webhooks.router,
            auth.router,
        ],
        cors_config=cors_config,
        compression_config=compression_config,
        openapi_config=openapi_config,
        dependencies={
            "plugin_manager": Provide(lambda: plugin_manager, sync_to_thread=False),
            "settings": Provide(lambda: settings, sync_to_thread=False),
        },
        debug=settings.debug,
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