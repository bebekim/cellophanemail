"""Billing and subscription routes."""
from litestar import Controller, get, post, Request, Response
from litestar.status_codes import HTTP_303_SEE_OTHER, HTTP_200_OK
from litestar.controller import Controller
from pydantic import BaseModel
from typing import Dict, Any
import logging

from ..services.stripe_service import StripeService
from ..middleware.jwt_auth import jwt_auth_required

logger = logging.getLogger(__name__)


class CheckoutRequest(BaseModel):
    """Stripe checkout request payload."""
    price_id: str


class BillingController(Controller):
    path = "/billing"
    tags = ["billing"]

    @post("/create-checkout", guards=[jwt_auth_required])
    async def create_checkout(self, request: Request, data: CheckoutRequest) -> Response:
        """Create Stripe Checkout session."""
        user = request.user
        stripe_service = StripeService()

        # Create or get customer
        if not user.stripe_customer_id:
            customer = await stripe_service.create_customer(
                user_id=str(user.id),
                email=user.email,
                name=f"{user.first_name or ''} {user.last_name or ''}".strip()
            )
            # Update user
            user.stripe_customer_id = customer.id
            await user.save()

        # Create checkout session
        session = await stripe_service.create_checkout_session(
            customer_id=user.stripe_customer_id,
            price_id=data.price_id,
            success_url=f"{request.base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.base_url}/billing/cancel",
            trial_days=30
        )

        return Response(
            content={"checkout_url": session.url},
            status_code=HTTP_200_OK
        )

    @get("/portal", guards=[jwt_auth_required])
    async def customer_portal(self, request: Request) -> Response:
        """Redirect to Stripe Customer Portal."""
        user = request.user
        stripe_service = StripeService()

        session = await stripe_service.create_portal_session(
            customer_id=user.stripe_customer_id,
            return_url=f"{request.base_url}/dashboard"
        )

        return Response(
            content={"portal_url": session.url},
            status_code=HTTP_303_SEE_OTHER,
            headers={"Location": session.url}
        )
