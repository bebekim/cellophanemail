"""Health check endpoints for CellophoneMail."""

from litestar import get
from litestar.controller import Controller
from typing import Dict, Any


class HealthController(Controller):
    """Health check and status endpoints."""
    
    path = "/health"
    
    @get("/")
    async def health_check(self) -> Dict[str, Any]:
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "service": "CellophoneMail",
            "version": "1.0.0",
            "framework": "Litestar",
            "features": {
                "four_horsemen_analysis": True,
                "plugin_architecture": True,
                "multi_tenant": True,
            }
        }
    
    @get("/ready")
    async def readiness_check(self) -> Dict[str, Any]:
        """Readiness check - verify all services are ready."""
        # TODO: Check database connection, Redis, plugins, etc.
        return {
            "status": "ready",
            "checks": {
                "database": "connected",
                "plugins": "loaded",
                "ai_service": "available",
            }
        }
    
    @get("/live") 
    async def liveness_check(self) -> Dict[str, str]:
        """Liveness check - minimal check for load balancers."""
        return {"status": "alive"}


# Export router for app registration
router = HealthController