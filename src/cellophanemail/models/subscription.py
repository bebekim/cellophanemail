"""Subscription model for CellophoneMail billing."""

from piccolo.table import Table
from piccolo.columns import (
    Varchar, Boolean, Timestamp, ForeignKey, UUID, JSON, Decimal
)
from datetime import datetime
import uuid
from enum import Enum
from .organization import Organization


class StripeSubscriptionStatus(Enum):
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class Subscription(Table, tablename="subscriptions"):
    """Stripe subscription tracking for organizations."""
    
    # Primary identification
    id = UUID(primary_key=True, default=uuid.uuid4)
    organization = ForeignKey(Organization, null=False, index=True)
    
    # Stripe integration
    stripe_subscription_id = Varchar(length=100, unique=True, null=False)
    stripe_customer_id = Varchar(length=100, null=False)
    stripe_product_id = Varchar(length=100, null=False)
    stripe_price_id = Varchar(length=100, null=False)
    
    # Subscription details
    status = Varchar(
        length=50,
        null=False,
        choices=StripeSubscriptionStatus
    )
    
    # Pricing
    amount = Decimal(digits=(10, 2), null=False)  # Price in cents
    currency = Varchar(length=3, default="aud")
    interval = Varchar(length=20, null=False)  # month, year
    
    # Trial & billing
    trial_start = Timestamp(null=True)
    trial_end = Timestamp(null=True)
    current_period_start = Timestamp(null=False)
    current_period_end = Timestamp(null=False)
    
    # Status tracking
    is_active = Boolean(default=True)
    canceled_at = Timestamp(null=True)
    cancel_at_period_end = Boolean(default=False)
    
    # Timestamps
    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(default=datetime.now)
    
    # Webhook metadata
    latest_invoice = JSON(null=True)
    payment_method = JSON(null=True)
    
    def __str__(self):
        return f"Subscription(org={self.organization}, status={self.status})"