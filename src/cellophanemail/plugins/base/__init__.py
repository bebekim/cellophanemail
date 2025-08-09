"""Base plugin interface for CellophoneMail plugins."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Abstract base class for all email processing plugins."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin with configuration."""
        self.config = config or {}
        self.name = "base"
        self.is_running = False
        
    @abstractmethod
    async def initialize(self):
        """Initialize the plugin with necessary resources."""
        pass
        
    @abstractmethod
    async def start(self):
        """Start the plugin and begin processing."""
        pass
        
    @abstractmethod
    async def stop(self):
        """Stop the plugin and cleanup resources."""
        pass
        
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return health status of the plugin."""
        pass
        
    async def reload_config(self, config: Dict[str, Any]):
        """Reload plugin configuration."""
        logger.info(f"Reloading configuration for {self.name} plugin")
        old_config = self.config
        self.config = config
        
        try:
            # Stop and restart with new config
            if self.is_running:
                await self.stop()
                await self.initialize()
                await self.start()
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")
            self.config = old_config
            raise


__all__ = ["BasePlugin"]