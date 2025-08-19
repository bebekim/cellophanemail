"""Data models for user accounts feature."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SubscriptionTier(Enum):
    """User subscription tiers."""
    FREE = "free"
    STARTER = "starter" 
    PROFESSIONAL = "professional"
    UNLIMITED = "unlimited"


class UserStatus(Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


@dataclass
class UserAccountInfo:
    """User account information."""
    user_id: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    shield_addresses: List[str] = None
    organization_id: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_verified: bool = False
    
    def __post_init__(self):
        if self.shield_addresses is None:
            self.shield_addresses = []


@dataclass
class UserRegistrationRequest:
    """Request to register a new user account."""
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_id: Optional[str] = None


@dataclass
class UserAuthRequest:
    """Request to authenticate a user."""
    email: str
    password: str


@dataclass
class UserAuthResult:
    """Result of user authentication."""
    success: bool
    user_info: Optional[UserAccountInfo] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ShieldAddressCreationResult:
    """Result of creating a shield address."""
    success: bool
    shield_address: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class UserPreferences:
    """User preferences and settings."""
    email_notifications: bool = True
    language: str = "en"
    timezone: str = "UTC"
    protection_level: str = "standard"
    custom_filters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_filters is None:
            self.custom_filters = {}


@dataclass
class UserUsageStats:
    """User usage statistics."""
    emails_processed_this_month: int
    emails_blocked_this_month: int
    shield_addresses_active: int
    api_requests_remaining: int
    storage_used_mb: float
    last_activity: Optional[datetime] = None