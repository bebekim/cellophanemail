"""Shield address management - self-contained feature."""

import logging
from typing import Optional, List
from datetime import datetime

from .models import ShieldAddressInfo

logger = logging.getLogger(__name__)


class ShieldAddressManager:
    """
    Manages shield addresses and user lookups.
    Self-contained feature that doesn't depend on external services.
    """
    
    def __init__(self):
        # In production, this would use a proper database
        # For now, we'll use a simple in-memory store for demo
        self._shield_addresses = {}
        self._initialize_demo_data()
    
    def _initialize_demo_data(self):
        """Initialize with some demo shield addresses for testing."""
        demo_addresses = [
            ShieldAddressInfo(
                shield_address="yh.kim@cellophanemail.com",
                user_id="user-001",
                user_email="yh.kim@gmail.com",
                organization_id="org-demo",
                created_at=datetime.now()
            ),
            ShieldAddressInfo(
                shield_address="recipient@cellophanemail.com", 
                user_id="user-002",
                user_email="recipient@example.com",
                organization_id="org-demo",
                created_at=datetime.now()
            ),
            ShieldAddressInfo(
                shield_address="shield123@cellophanemail.com",
                user_id="user-003", 
                user_email="demo@example.com",
                organization_id=None,
                created_at=datetime.now()
            ),
            ShieldAddressInfo(
                shield_address="shield456@cellophanemail.com",
                user_id="user-004",
                user_email="test456@example.com", 
                organization_id=None,
                created_at=datetime.now()
            ),
            ShieldAddressInfo(
                shield_address="shield789@cellophanemail.com",
                user_id="user-005",
                user_email="test789@example.com",
                organization_id=None,
                created_at=datetime.now()
            )
        ]
        
        for addr_info in demo_addresses:
            self._shield_addresses[addr_info.shield_address] = addr_info
            
        logger.info(f"Initialized {len(demo_addresses)} demo shield addresses")
    
    async def lookup_user_by_shield_address(self, shield_address: str) -> Optional[ShieldAddressInfo]:
        """
        Look up user information by shield address.
        
        Args:
            shield_address: The shield address to look up
            
        Returns:
            ShieldAddressInfo if found and active, None otherwise
        """
        shield_address = shield_address.lower().strip()
        
        logger.info(f"Looking up shield address: {shield_address}")
        
        if shield_address in self._shield_addresses:
            addr_info = self._shield_addresses[shield_address]
            
            if addr_info.is_active:
                # Update last used timestamp
                addr_info.last_used = datetime.now()
                logger.info(f"Found active user {addr_info.user_id} for shield {shield_address}")
                return addr_info
            else:
                logger.warning(f"Shield address {shield_address} exists but is inactive")
                return None
        else:
            logger.warning(f"Shield address {shield_address} not found")
            return None
    
    async def create_shield_address(
        self, 
        user_id: str, 
        user_email: str,
        organization_id: Optional[str] = None
    ) -> ShieldAddressInfo:
        """
        Create a new shield address for a user.
        
        Args:
            user_id: The user's ID
            user_email: The user's real email address
            organization_id: Optional organization ID
            
        Returns:
            ShieldAddressInfo for the created address
        """
        # Generate a unique shield address
        # In production, this would be more sophisticated
        import secrets
        unique_part = secrets.token_hex(8)
        shield_address = f"shield-{unique_part}@cellophanemail.com"
        
        addr_info = ShieldAddressInfo(
            shield_address=shield_address,
            user_id=user_id,
            user_email=user_email,
            organization_id=organization_id,
            created_at=datetime.now()
        )
        
        self._shield_addresses[shield_address] = addr_info
        
        logger.info(f"Created shield address {shield_address} for user {user_id}")
        return addr_info
    
    async def deactivate_shield_address(self, shield_address: str) -> bool:
        """
        Deactivate a shield address.
        
        Args:
            shield_address: The shield address to deactivate
            
        Returns:
            True if deactivated, False if not found
        """
        shield_address = shield_address.lower().strip()
        
        if shield_address in self._shield_addresses:
            self._shield_addresses[shield_address].is_active = False
            logger.info(f"Deactivated shield address {shield_address}")
            return True
        else:
            logger.warning(f"Cannot deactivate - shield address {shield_address} not found")
            return False
    
    async def list_user_shield_addresses(self, user_id: str) -> List[ShieldAddressInfo]:
        """
        List all shield addresses for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of ShieldAddressInfo for the user
        """
        user_addresses = [
            addr_info for addr_info in self._shield_addresses.values()
            if addr_info.user_id == user_id
        ]
        
        logger.info(f"Found {len(user_addresses)} shield addresses for user {user_id}")
        return user_addresses