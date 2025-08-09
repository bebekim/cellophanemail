"""SMTP Plugin implementation."""

import asyncio
import logging
from typing import Optional, Dict, Any

from ..base import BasePlugin
from .server import SMTPServerRunner

logger = logging.getLogger(__name__)


class SMTPPlugin(BasePlugin):
    """SMTP plugin for receiving emails via SMTP protocol."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize SMTP plugin with configuration."""
        super().__init__(config)
        self.name = "smtp"
        self.server = None
        self.server_task = None
        
    async def initialize(self):
        """Initialize the SMTP plugin."""
        logger.info("Initializing SMTP plugin")
        
        # Get configuration
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 2525)
        
        # Create server instance
        self.server = SMTPServerRunner(host=host, port=port)
        logger.info(f"SMTP plugin initialized for {host}:{port}")
        
    async def start(self):
        """Start the SMTP server."""
        if not self.server:
            await self.initialize()
            
        logger.info("Starting SMTP plugin")
        
        # Start server in background task
        self.server_task = asyncio.create_task(self.server.run_forever())
        self.is_running = True
        
        logger.info("SMTP plugin started successfully")
        
    async def stop(self):
        """Stop the SMTP server."""
        logger.info("Stopping SMTP plugin")
        
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
                
        if self.server:
            await self.server.stop()
            
        self.is_running = False
        logger.info("SMTP plugin stopped")
        
    async def health_check(self) -> Dict[str, Any]:
        """Check health of SMTP plugin."""
        return {
            "plugin": self.name,
            "status": "healthy" if self.is_running else "stopped",
            "host": self.server.host if self.server else None,
            "port": self.server.port if self.server else None,
        }