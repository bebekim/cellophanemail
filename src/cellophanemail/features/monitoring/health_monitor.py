"""
Health Monitoring System for Privacy-Focused Email Processing

Comprehensive health checking for all components with Kubernetes probe support,
component failure detection, and dependency monitoring.
"""

import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of individual component."""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    last_check: float
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class HealthCheckResult:
    """Result of overall health check."""
    is_healthy: bool
    components: Dict[str, ComponentHealth]
    timestamp: float
    overall_status: HealthStatus
    failed_components: List[str]
    
    def __post_init__(self):
        """Calculate derived properties."""
        self.failed_components = [
            name for name, health in self.components.items()
            if health.status == HealthStatus.UNHEALTHY
        ]
        
        # Determine overall status
        if self.failed_components:
            self.overall_status = HealthStatus.UNHEALTHY
            self.is_healthy = False
        elif any(health.status == HealthStatus.DEGRADED for health in self.components.values()):
            self.overall_status = HealthStatus.DEGRADED
            self.is_healthy = True  # Still accepting traffic
        else:
            self.overall_status = HealthStatus.HEALTHY
            self.is_healthy = True


class HealthCheck(ABC):
    """Abstract interface for component health checks."""
    
    @abstractmethod
    async def check_health(self) -> ComponentHealth:
        """Perform health check and return result."""
        pass
    
    @abstractmethod
    def get_component_name(self) -> str:
        """Get the name of this component."""
        pass
    
    def get_dependencies(self) -> List[str]:
        """Get list of dependencies for this component."""
        return []


class DatabaseHealthCheck(HealthCheck):
    """Health check for database connection."""
    
    async def check_health(self) -> ComponentHealth:
        """Check database connectivity."""
        start_time = time.time()
        
        try:
            # Mock database check - in real implementation, use actual database
            await self._check_database_connection()
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                response_time_ms=response_time,
                last_check=time.time(),
                details={"connection_pool_size": 10, "active_connections": 3}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=response_time,
                last_check=time.time(),
                details={"error": str(e)}
            )
    
    async def _check_database_connection(self):
        """Mock database connection check."""
        # In real implementation, perform actual database ping
        await asyncio.sleep(0.01)  # Simulate network call
        # Simulate occasional failure for testing
        import random
        if random.random() < 0.1:  # 10% failure rate for testing
            raise ConnectionError("Database connection timeout")
    
    def get_component_name(self) -> str:
        return "database"


class MemoryManagerHealthCheck(HealthCheck):
    """Health check for memory manager component."""
    
    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
    
    async def check_health(self) -> ComponentHealth:
        """Check memory manager health."""
        start_time = time.time()
        
        try:
            if self.memory_manager:
                stats = self.memory_manager.get_stats()
                current_emails = stats.get('current_emails', 0)
                max_concurrent = stats.get('max_concurrent', 50)
                
                # Check if approaching capacity
                utilization = current_emails / max_concurrent
                if utilization > 0.9:
                    status = HealthStatus.DEGRADED
                    message = f"Memory manager at {utilization:.1%} capacity"
                elif utilization > 0.95:
                    status = HealthStatus.UNHEALTHY
                    message = f"Memory manager critically full at {utilization:.1%}"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Memory manager healthy ({current_emails}/{max_concurrent} emails)"
                
                details = {
                    "current_emails": current_emails,
                    "max_concurrent": max_concurrent,
                    "utilization": utilization,
                    "available_slots": max_concurrent - current_emails
                }
            else:
                status = HealthStatus.HEALTHY
                message = "Memory manager not initialized (test mode)"
                details = {}
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="memory_manager",
                status=status,
                message=message,
                response_time_ms=response_time,
                last_check=time.time(),
                details=details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="memory_manager",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory manager check failed: {str(e)}",
                response_time_ms=response_time,
                last_check=time.time(),
                details={"error": str(e)}
            )
    
    def get_component_name(self) -> str:
        return "memory_manager"


class LLMAnalyzerHealthCheck(HealthCheck):
    """Health check for LLM analyzer component."""
    
    async def check_health(self) -> ComponentHealth:
        """Check LLM analyzer availability."""
        start_time = time.time()
        
        try:
            # Mock LLM analyzer check - in real implementation, test actual analyzer
            await self._test_llm_analyzer()
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="llm_analyzer", 
                status=HealthStatus.HEALTHY,
                message="LLM analyzer responding normally",
                response_time_ms=response_time,
                last_check=time.time(),
                details={"provider": "anthropic", "model": "claude-3-sonnet"}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="llm_analyzer",
                status=HealthStatus.UNHEALTHY,
                message=f"LLM analyzer unavailable: {str(e)}",
                response_time_ms=response_time,
                last_check=time.time(),
                details={"error": str(e)}
            )
    
    async def _test_llm_analyzer(self):
        """Mock LLM analyzer test."""
        # In real implementation, send test prompt to LLM
        await asyncio.sleep(0.05)  # Simulate API call
        import random
        if random.random() < 0.05:  # 5% failure rate
            raise TimeoutError("LLM API timeout")
    
    def get_component_name(self) -> str:
        return "llm_analyzer"
    
    def get_dependencies(self) -> List[str]:
        return ["internet_connection", "api_keys"]


class EmailDeliveryHealthCheck(HealthCheck):
    """Health check for email delivery service."""
    
    async def check_health(self) -> ComponentHealth:
        """Check email delivery service health."""
        start_time = time.time()
        
        try:
            # Mock delivery service check
            await self._check_delivery_service()
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="email_delivery",
                status=HealthStatus.HEALTHY,
                message="Email delivery service operational",
                response_time_ms=response_time,
                last_check=time.time(),
                details={"provider": "postmark", "queue_size": 0}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="email_delivery",
                status=HealthStatus.DEGRADED,
                message=f"Delivery service issues: {str(e)}",
                response_time_ms=response_time,
                last_check=time.time(),
                details={"error": str(e)}
            )
    
    async def _check_delivery_service(self):
        """Mock delivery service check."""
        await asyncio.sleep(0.02)
        import random
        if random.random() < 0.15:  # 15% degradation rate
            raise ConnectionError("SMTP server slow response")
    
    def get_component_name(self) -> str:
        return "email_delivery"


class BackgroundTasksHealthCheck(HealthCheck):
    """Health check for background tasks."""
    
    async def check_health(self) -> ComponentHealth:
        """Check background task health."""
        start_time = time.time()
        
        try:
            # Mock background tasks check
            cleanup_last_run = time.time() - 45  # 45 seconds ago
            max_interval = 60  # Should run every 60 seconds
            
            if time.time() - cleanup_last_run > max_interval * 2:
                status = HealthStatus.UNHEALTHY
                message = "Background cleanup tasks not running"
            elif time.time() - cleanup_last_run > max_interval * 1.5:
                status = HealthStatus.DEGRADED
                message = "Background cleanup tasks delayed"
            else:
                status = HealthStatus.HEALTHY
                message = "Background tasks running normally"
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="background_tasks",
                status=status,
                message=message,
                response_time_ms=response_time,
                last_check=time.time(),
                details={
                    "cleanup_last_run": cleanup_last_run,
                    "cleanup_interval": max_interval
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="background_tasks",
                status=HealthStatus.UNHEALTHY,
                message=f"Background task check failed: {str(e)}",
                response_time_ms=response_time,
                last_check=time.time(),
                details={"error": str(e)}
            )
    
    def get_component_name(self) -> str:
        return "background_tasks"


class HealthMonitor:
    """
    Comprehensive health monitoring system for privacy-focused email processing.
    
    Provides health checks for all components, Kubernetes probe endpoints,
    and failure detection with detailed diagnostics.
    """
    
    def __init__(self, memory_manager=None, cache_ttl: int = 30, check_timeout: float = 10.0):
        """Initialize health monitor with configurable caching and timeouts."""
        self.health_checks: List[HealthCheck] = [
            DatabaseHealthCheck(),
            MemoryManagerHealthCheck(memory_manager),
            LLMAnalyzerHealthCheck(),
            EmailDeliveryHealthCheck(),
            BackgroundTasksHealthCheck()
        ]
        
        self._last_health_check: Optional[HealthCheckResult] = None
        self._health_check_cache_ttl = cache_ttl  # Configurable cache TTL
        self._check_timeout = check_timeout  # Timeout for individual checks
        
        # Performance tracking
        self._check_count = 0
        self._total_check_time = 0.0
    
    async def check_all_components_async(self) -> HealthCheckResult:
        """Perform health check on all components asynchronously."""
        start_time = time.time()
        
        # Run all health checks concurrently
        health_check_tasks = [
            health_check.check_health() for health_check in self.health_checks
        ]
        
        try:
            component_results = await asyncio.gather(*health_check_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            # Return unhealthy status
            return HealthCheckResult(
                is_healthy=False,
                components={},
                timestamp=time.time(),
                overall_status=HealthStatus.UNHEALTHY,
                failed_components=[]
            )
        
        # Process results
        components = {}
        for i, result in enumerate(component_results):
            if isinstance(result, Exception):
                component_name = self.health_checks[i].get_component_name()
                components[component_name] = ComponentHealth(
                    name=component_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check exception: {str(result)}",
                    response_time_ms=0,
                    last_check=time.time()
                )
            else:
                components[result.name] = result
        
        health_result = HealthCheckResult(
            is_healthy=True,  # Will be calculated in __post_init__
            components=components,
            timestamp=time.time(),
            overall_status=HealthStatus.HEALTHY,  # Will be calculated
            failed_components=[]  # Will be calculated
        )
        
        # Cache the result
        self._last_health_check = health_result
        
        return health_result
    
    def get_overall_health(self) -> HealthCheckResult:
        """Get overall health status (synchronous, uses cache if recent)."""
        current_time = time.time()
        
        # Return cached result if recent
        if (self._last_health_check and 
            current_time - self._last_health_check.timestamp < self._health_check_cache_ttl):
            return self._last_health_check
        
        # For synchronous call, return basic health check
        components = {}
        for health_check in self.health_checks:
            component_name = health_check.get_component_name()
            components[component_name] = ComponentHealth(
                name=component_name,
                status=HealthStatus.HEALTHY,
                message="Synchronous check - status assumed healthy",
                response_time_ms=0,
                last_check=current_time
            )
        
        return HealthCheckResult(
            is_healthy=True,
            components=components,
            timestamp=current_time,
            overall_status=HealthStatus.HEALTHY,
            failed_components=[]
        )
    
    def get_liveness_status(self) -> Dict[str, Any]:
        """Get liveness probe status for Kubernetes."""
        # Liveness should only check if the service is running
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime_seconds": time.time() - getattr(self, '_start_time', time.time()),
            "version": "1.0.0"
        }
    
    def get_readiness_status(self) -> Dict[str, Any]:
        """Get readiness probe status for Kubernetes."""
        # Readiness should check if the service can handle traffic
        health_status = self.get_overall_health()
        
        # Check critical dependencies
        critical_components = ['database', 'memory_manager', 'llm_analyzer']
        dependencies = {}
        ready = True
        
        for component_name in critical_components:
            if component_name in health_status.components:
                component = health_status.components[component_name]
                dependencies[component_name] = {
                    "status": component.status.value,
                    "message": component.message
                }
                if component.status == HealthStatus.UNHEALTHY:
                    ready = False
            else:
                dependencies[component_name] = {
                    "status": "unknown",
                    "message": "Component not found"
                }
                ready = False
        
        return {
            "status": "ready" if ready else "not_ready",
            "dependencies": dependencies,
            "timestamp": time.time(),
            "overall_healthy": health_status.is_healthy
        }


# Helper functions for external integrations
async def check_database_connection():
    """Check database connection (implementation placeholder)."""
    # In real implementation, perform actual database ping
    await asyncio.sleep(0.01)
    import random
    if random.random() < 0.1:
        raise ConnectionError("Database connection failed")