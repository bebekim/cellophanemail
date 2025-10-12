"""Stripe webhook event handler."""
from litestar import Controller, post, Request, Response
from litestar.status_codes import HTTP_200_OK
from litestar.controller import Controller
from typing import Dict, Any
from datetime import datetime
import logging

from ..services.stripe_service import StripeService
from ..models.subscription import Subscription
from ..models.user import User

logger = logging.getLogger(__name__)


class StripeWebhookHandler(Controller):
    path = "/webhooks/stripe"
    tags = ["webhooks"]

    @post("/")
    async def handle_webhook(self, request: Request) -> Response:
        """Handle Stripe webhook events."""
        stripe_service = StripeService()

        # Verify signature
        payload = await request.body()
        sig_header = request.headers.get("Stripe-Signature")

        try:
            event = stripe_service.verify_webhook_signature(payload, sig_header)
        except Exception as e:
            logger.error(f"Stripe webhook signature verification failed: {e}")
            return Response(content={"error": "Invalid signature"}, status_code=400)

        # Handle events
        event_type = event["type"]
        data_object = event["data"]["object"]

        logger.info(f"Received Stripe webhook event: {event_type}")

        if event_type == "customer.subscription.created":
            await self._handle_subscription_created(data_object)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(data_object)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(data_object)
        elif event_type == "invoice.payment_succeeded":
            await self._handle_payment_succeeded(data_object)
        elif event_type == "invoice.payment_failed":
            await self._handle_payment_failed(data_object)

        return Response(content={"received": True}, status_code=HTTP_200_OK)

    async def _handle_subscription_created(self, subscription: Dict[str, Any]):
        """Create subscription record in database."""
        # Find user by customer_id
        user = await User.objects().where(
            User.stripe_customer_id == subscription["customer"]
        ).first()

        if user:
            # Get subscription plan details
            plan = subscription["items"]["data"][0]["price"]

            await Subscription.objects().create(
                organization_id=user.organization_id,
                stripe_subscription_id=subscription["id"],
                stripe_customer_id=subscription["customer"],
                stripe_product_id=plan["product"],
                stripe_price_id=plan["id"],
                status=subscription["status"],
                amount=plan["unit_amount"] / 100,  # Convert cents to dollars
                currency=plan["currency"],
                interval=plan["recurring"]["interval"],
                current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                trial_start=datetime.fromtimestamp(subscription["trial_start"]) if subscription.get("trial_start") else None,
                trial_end=datetime.fromtimestamp(subscription["trial_end"]) if subscription.get("trial_end") else None
            )

            # Update user subscription status
            user.subscription_status = "active"
            await user.save()

            logger.info(f"Created subscription for user {user.email}")

    async def _handle_subscription_updated(self, subscription: Dict[str, Any]):
        """Update existing subscription record."""
        sub = await Subscription.objects().where(
            Subscription.stripe_subscription_id == subscription["id"]
        ).first()

        if sub:
            sub.status = subscription["status"]
            sub.current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
            sub.current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
            sub.cancel_at_period_end = subscription.get("cancel_at_period_end", False)

            if subscription.get("canceled_at"):
                sub.canceled_at = datetime.fromtimestamp(subscription["canceled_at"])

            await sub.save()

            # Update user status
            user = await User.objects().where(
                User.stripe_customer_id == subscription["customer"]
            ).first()

            if user:
                user.subscription_status = subscription["status"]
                await user.save()

            logger.info(f"Updated subscription {subscription['id']}")

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]):
        """Handle subscription cancellation."""
        sub = await Subscription.objects().where(
            Subscription.stripe_subscription_id == subscription["id"]
        ).first()

        if sub:
            sub.status = "canceled"
            sub.is_active = False
            sub.canceled_at = datetime.now()
            await sub.save()

            # Update user status
            user = await User.objects().where(
                User.stripe_customer_id == subscription["customer"]
            ).first()

            if user:
                user.subscription_status = "canceled"
                await user.save()

            logger.info(f"Canceled subscription {subscription['id']}")

    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]):
        """Handle successful payment."""
        logger.info(f"Payment succeeded for invoice {invoice['id']}")
        # Could add invoice tracking here if needed

    async def _handle_payment_failed(self, invoice: Dict[str, Any]):
        """Handle failed payment."""
        customer_id = invoice["customer"]

        # Update user to past_due status
        user = await User.objects().where(
            User.stripe_customer_id == customer_id
        ).first()

        if user:
            user.subscription_status = "past_due"
            await user.save()
            logger.warning(f"Payment failed for user {user.email}")
