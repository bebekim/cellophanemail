"""Stripe billing service."""
import stripe
import logging
from typing import Optional, Dict, Any
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class StripeService:
    """Handle all Stripe API interactions."""

    def __init__(self):
        settings = get_settings()
        stripe.api_key = settings.stripe_api_key
        self.webhook_secret = settings.stripe_webhook_secret

    async def create_customer(self, user_id: str, email: str, name: str) -> stripe.Customer:
        """Create Stripe customer."""
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata={"user_id": user_id}
        )

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 30
    ) -> stripe.checkout.Session:
        """Create Stripe Checkout session."""
        return stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={"trial_period_days": trial_days},
            allow_promotion_codes=True
        )

    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> stripe.Subscription:
        """Cancel subscription."""
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=at_period_end
        )

    async def create_portal_session(self, customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """Create Stripe Customer Portal session."""
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature."""
        return stripe.Webhook.construct_event(
            payload, sig_header, self.webhook_secret
        )
