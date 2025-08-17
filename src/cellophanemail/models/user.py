"""User model for CellophoneMail SaaS."""

from piccolo.table import Table
from piccolo.columns import (
    Varchar, Text, Boolean, Timestamp, ForeignKey, UUID, JSON
)
from datetime import datetime
import uuid
from enum import Enum
from .organization import Organization


class SubscriptionStatus(Enum):
    FREE = "free"
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class User(Table, tablename="users"):
    """SaaS user model with authentication and billing."""
    
    # Primary identification
    id = UUID(primary_key=True, default=uuid.uuid4)
    email = Varchar(length=255, unique=True, index=True, null=False)
    username = Varchar(length=100, unique=True, index=True, null=True)
    
    # Authentication
    hashed_password = Varchar(length=255, null=True)  # Null for OAuth-only users
    oauth_provider = Varchar(length=50, null=True)  # e.g., 'google', 'github', etc.
    oauth_id = Varchar(length=255, null=True)  # Provider-specific user ID
    is_active = Boolean(default=True)
    is_verified = Boolean(default=False)
    verification_token = Varchar(length=255, null=True)
    
    # Profile
    first_name = Varchar(length=100, null=True)
    last_name = Varchar(length=100, null=True)
    avatar_url = Text(null=True)
    
    # Billing & subscription
    organization = ForeignKey(Organization, null=True)
    stripe_customer_id = Varchar(length=100, null=True)
    subscription_status = Varchar(
        length=50, 
        default=SubscriptionStatus.FREE, 
        choices=SubscriptionStatus
    )
    
    # Usage tracking
    emails_processed_month = JSON(default={"count": 0, "reset_date": None})
    api_quota_remaining = JSON(default={"requests": 1000, "reset_date": None})
    
    # Timestamps
    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(default=datetime.now)
    last_login = Timestamp(null=True)
    
    # Settings
    preferences = JSON(default={
        "email_notifications": True,
        "language": "en",
        "timezone": "Australia/Melbourne"
    })
    
    def __str__(self):
        return f"User(email={self.email}, active={self.is_active})"