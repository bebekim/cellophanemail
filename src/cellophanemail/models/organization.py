"""Organization model for CellophoneMail multi-tenant SaaS."""

from piccolo.table import Table
from piccolo.columns import (
    Varchar, Text, Boolean, Timestamp, UUID, JSON, Integer
)
from datetime import datetime
import uuid
from enum import Enum


class SubscriptionPlan(Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class OrganizationStatus(Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class Organization(Table, tablename="organizations"):
    """Multi-tenant organization model for SaaS."""
    
    # Primary identification
    id = UUID(primary_key=True, default=uuid.uuid4)
    name = Varchar(length=255, null=False, index=True)
    slug = Varchar(length=100, unique=True, index=True, null=False)
    
    # Organization details
    description = Text(null=True)
    website = Varchar(length=500, null=True)
    logo_url = Text(null=True)
    
    # Billing
    stripe_customer_id = Varchar(length=100, null=True)
    subscription_plan = Varchar(
        length=50,
        default=SubscriptionPlan.FREE,
        choices=SubscriptionPlan
    )
    subscription_status = Varchar(
        length=50,
        default=OrganizationStatus.ACTIVE,
        choices=OrganizationStatus
    )
    
    # Usage & limits
    monthly_email_limit = Integer(default=1000)
    emails_processed_month = Integer(default=0)
    user_limit = Integer(default=5)
    
    # Status
    is_active = Boolean(default=True)
    is_verified = Boolean(default=False)
    
    # Timestamps
    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(default=datetime.now)
    
    # Organization settings
    settings = JSON(default={
        "timezone": "Australia/Melbourne",
        "email_retention_days": 30,
        "webhooks_enabled": True,
        "ai_analysis_enabled": True
    })
    
    def __str__(self):
        return f"Organization(name={self.name}, plan={self.subscription_plan})"