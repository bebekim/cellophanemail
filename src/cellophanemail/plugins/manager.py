"""Plugin manager for email input methods."""

from typing import Dict, Any, List, Optional
import logging
import asyncio

from .base import BasePlugin
from .smtp import SMTPPlugin
# Future imports:
# from .postmark import PostmarkPlugin
# from .gmail_api import GmailAPIPlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages email input plugins lifecycle."""
    
    # Registry of available plugins
    AVAILABLE_PLUGINS = {
        "smtp": SMTPPlugin,
        # "postmark": PostmarkPlugin,
        # "gmail": GmailAPIPlugin,
    }
    
    def __init__(self):
        """Initialize plugin manager."""
        self.plugins: Dict[str, BasePlugin] = {}
        self.active_plugins: List[str] = []
        logger.info("Plugin manager initialized")
    
    async def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Load a single plugin with configuration."""
        if plugin_name not in self.AVAILABLE_PLUGINS:
            raise ValueError(f"Unknown plugin: {plugin_name}")
            
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} already loaded")
            return
            
        try:
            logger.info(f"Loading plugin: {plugin_name}")
            
            # Create plugin instance
            plugin_class = self.AVAILABLE_PLUGINS[plugin_name]
            plugin = plugin_class(config or {})
            
            # Initialize plugin
            await plugin.initialize()
            
            # Store plugin
            self.plugins[plugin_name] = plugin
            logger.info(f"Plugin {plugin_name} loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
            raise
    
    async def load_plugins(self, plugin_configs: Dict[str, Dict[str, Any]]) -> None:
        """Load multiple plugins with their configurations."""
        for plugin_name, config in plugin_configs.items():
            await self.load_plugin(plugin_name, config)
        
        logger.info(f"Loaded {len(plugin_configs)} plugins")
    
    async def start_plugin(self, plugin_name: str) -> None:
        """Start a single plugin."""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not loaded")
            
        plugin = self.plugins[plugin_name]
        if plugin.is_running:
            logger.warning(f"Plugin {plugin_name} already running")
            return
            
        try:
            logger.info(f"Starting plugin: {plugin_name}")
            await plugin.start()
            self.active_plugins.append(plugin_name)
            logger.info(f"Plugin {plugin_name} started successfully")
        except Exception as e:
            logger.error(f"Failed to start plugin {plugin_name}: {e}", exc_info=True)
            raise
    
    async def start_plugins(self) -> None:
        """Start all loaded plugins."""
        logger.info("Starting all plugins...")
        
        tasks = []
        for plugin_name in self.plugins:
            tasks.append(self.start_plugin(plugin_name))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for errors
        for plugin_name, result in zip(self.plugins.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Failed to start {plugin_name}: {result}")
                
        logger.info(f"Started {len(self.active_plugins)} plugins")
    
    async def stop_plugin(self, plugin_name: str) -> None:
        """Stop a single plugin."""
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} not found")
            return
            
        plugin = self.plugins[plugin_name]
        if not plugin.is_running:
            logger.warning(f"Plugin {plugin_name} not running")
            return
            
        try:
            logger.info(f"Stopping plugin: {plugin_name}")
            await plugin.stop()
            if plugin_name in self.active_plugins:
                self.active_plugins.remove(plugin_name)
            logger.info(f"Plugin {plugin_name} stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop plugin {plugin_name}: {e}", exc_info=True)
    
    async def stop_plugins(self) -> None:
        """Stop all plugins gracefully."""
        logger.info("Stopping all plugins...")
        
        tasks = []
        for plugin_name in list(self.active_plugins):
            tasks.append(self.stop_plugin(plugin_name))
            
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("All plugins stopped")
    
    async def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins."""
        status = {}
        
        for plugin_name, plugin in self.plugins.items():
            try:
                health = await plugin.health_check()
                status[plugin_name] = health
            except Exception as e:
                status[plugin_name] = {
                    "status": "error",
                    "error": str(e)
                }
                
        return status
    
    async def reload_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Reload configuration for a specific plugin."""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not loaded")
            
        plugin = self.plugins[plugin_name]
        await plugin.reload_config(config)