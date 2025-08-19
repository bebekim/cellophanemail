"""Models for shield address management."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ShieldAddressInfo:
    """Information about a shield address and its associated user."""
    shield_address: str
    user_id: str
    user_email: str
    organization_id: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "shield_address": self.shield_address,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "organization_id": self.organization_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }