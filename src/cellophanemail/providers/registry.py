"""License-aware provider registry for email providers."""

import os
import logging
from enum import Enum
from typing import Dict, Type, Optional, List, Any
from importlib import import_module
from .contracts import EmailProvider, ProviderConfig

logger = logging.getLogger(__name__)


class LicenseType(Enum):
    """Types of licenses for providers."""
    OPEN_SOURCE = "open_source"
    COMMERCIAL = "commercial"
    ENTERPRISE = "enterprise"


class ProviderRegistry:
    """
    Registry for managing email providers with license awareness.
    This allows us to control which providers are available based on license.
    """
    
    # Provider metadata - defines what's available and licensing requirements
    _providers: Dict[str, Dict[str, Any]] = {
        "gmail": {
            "module": "cellophanemail.providers.gmail.provider",
            "class": "GmailProvider",
            "license": LicenseType.OPEN_SOURCE,
            "description": "Gmail API integration (OAuth2)",
            "features": ["oauth", "webhooks", "labels"]
        },
        "smtp": {
            "module": "cellophanemail.providers.smtp.provider",
            "class": "SMTPProvider",
            "license": LicenseType.OPEN_SOURCE,
            "description": "SMTP server integration",
            "features": ["embedded_server", "direct_send"]
        },
        "postmark": {
            "module": "cellophanemail.providers.postmark.provider",
            "class": "PostmarkProvider",
            "license": LicenseType.COMMERCIAL,
            "description": "Postmark commercial email service",
            "features": ["webhooks", "analytics", "templates", "priority_support"]
        }
    }
    
    def __init__(self, license_key: Optional[str] = None):
        """
        Initialize registry with optional license key.
        
        Args:
            license_key: Commercial license key if available
        """
        self.license_key = license_key or os.getenv("CELLOPHANEMAIL_LICENSE_KEY")
        self.license_type = self._determine_license_type()
        self._loaded_providers: Dict[str, EmailProvider] = {}
        
    def _determine_license_type(self) -> LicenseType:
        """Determine current license type based on license key."""
        if not self.license_key:
            return LicenseType.OPEN_SOURCE
            
        # Simple license key validation
        # In production, this would validate with license server
        if self.license_key.startswith("ENT-"):
            return LicenseType.ENTERPRISE
        elif self.license_key.startswith("COM-"):
            return LicenseType.COMMERCIAL
        else:
            logger.warning(f"Invalid license key format: {self.license_key[:10]}...")
            return LicenseType.OPEN_SOURCE
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """
        Get list of providers available with current license.
        
        Returns:
            List of provider info dicts with name, description, and features
        """
        available = []
        for name, info in self._providers.items():
            if self._is_provider_licensed(info["license"]):
                available.append({
                    "name": name,
                    "description": info["description"],
                    "features": info["features"],
                    "license_required": info["license"].value
                })
        return available
    
    def get_provider(self, name: str, config: Optional[ProviderConfig] = None) -> EmailProvider:
        """
        Get or create a provider instance.
        
        Args:
            name: Provider name (gmail, smtp, postmark)
            config: Optional provider configuration
            
        Returns:
            Initialized provider instance
            
        Raises:
            ValueError: If provider not found or not licensed
        """
        # Check if provider exists
        if name not in self._providers:
            available = ", ".join(self._providers.keys())
            raise ValueError(f"Unknown provider: {name}. Available: {available}")
        
        provider_info = self._providers[name]
        
        # Check license
        if not self._is_provider_licensed(provider_info["license"]):
            raise ValueError(
                f"Provider '{name}' requires {provider_info['license'].value} license. "
                f"Current license: {self.license_type.value}. "
                f"Visit https://cellophanemail.com/pricing to upgrade."
            )
        
        # Return cached instance if available and no new config
        if name in self._loaded_providers and not config:
            return self._loaded_providers[name]
        
        # Load provider class dynamically
        try:
            module = import_module(provider_info["module"])
            provider_class = getattr(module, provider_info["class"])
            
            # Create instance
            provider = provider_class()
            
            # Initialize if config provided
            if config:
                import asyncio
                if asyncio.iscoroutinefunction(provider.initialize):
                    # Handle async initialization
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(provider.initialize(config))
                else:
                    provider.initialize(config)
            
            # Cache for reuse
            self._loaded_providers[name] = provider
            
            logger.info(f"Loaded provider: {name} ({provider_info['description']})")
            return provider
            
        except ImportError as e:
            logger.error(f"Failed to import provider {name}: {e}")
            raise ValueError(f"Provider {name} not installed or import failed: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize provider {name}: {e}")
            raise
    
    def _is_provider_licensed(self, required_license: LicenseType) -> bool:
        """Check if current license allows access to provider."""
        if required_license == LicenseType.OPEN_SOURCE:
            return True  # Always available
        
        if self.license_type == LicenseType.ENTERPRISE:
            return True  # Enterprise can access everything
            
        if self.license_type == LicenseType.COMMERCIAL:
            return required_license in [LicenseType.COMMERCIAL, LicenseType.OPEN_SOURCE]
            
        return False  # Open source can't access commercial/enterprise
    
    def get_provider_info(self, name: str) -> Dict[str, Any]:
        """Get information about a specific provider."""
        if name not in self._providers:
            raise ValueError(f"Unknown provider: {name}")
            
        info = self._providers[name].copy()
        info["name"] = name
        info["available"] = self._is_provider_licensed(info["license"])
        info["license"] = info["license"].value
        return info
    
    def list_all_providers(self) -> List[Dict[str, Any]]:
        """List all providers with availability status."""
        providers = []
        for name in self._providers:
            providers.append(self.get_provider_info(name))
        return providers


# Global registry instance
_registry: Optional[ProviderRegistry] = None


def get_provider_registry(license_key: Optional[str] = None) -> ProviderRegistry:
    """
    Get or create the global provider registry.
    
    Args:
        license_key: Optional license key to use
        
    Returns:
        Global ProviderRegistry instance
    """
    global _registry
    if _registry is None or license_key:
        _registry = ProviderRegistry(license_key)
    return _registry


def get_provider(name: str, config: Optional[ProviderConfig] = None) -> EmailProvider:
    """
    Convenience function to get a provider from the global registry.
    
    Args:
        name: Provider name
        config: Optional configuration
        
    Returns:
        Provider instance
    """
    return get_provider_registry().get_provider(name, config)