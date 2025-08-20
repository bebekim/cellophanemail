"""Core plugin infrastructure for CellophoneMail."""

from .registry import PluginRegistry, get_plugin_registry
from .loader import PluginLoader
from .manifest import PluginManifest, PluginCapabilities
from .discovery import PluginDiscovery

__all__ = [
    "PluginRegistry",
    "get_plugin_registry", 
    "PluginLoader",
    "PluginManifest",
    "PluginCapabilities",
    "PluginDiscovery"
]