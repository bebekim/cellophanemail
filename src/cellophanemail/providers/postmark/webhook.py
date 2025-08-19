"""Postmark webhook handler."""

import logging
from typing import Dict, Any, Optional

from litestar import post, Response, Request
from litestar.controller import Controller
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from pydantic import BaseModel

from .provider import PostmarkProvider
from ..contracts import EmailMessage
from ...features.email_protection import EmailProtectionProcessor

logger = logging.getLogger(__name__)


class PostmarkWebhookPayload(BaseModel):
    """Postmark inbound webhook payload structure."""
    From: str
    FromName: Optional[str] = None
    To: str
    ToFull: Optional[list[Dict[str, str]]] = None
    Subject: str
    MessageID: str
    Date: str
    TextBody: Optional[str] = None
    HtmlBody: Optional[str] = None
    Tag: Optional[str] = None
    Headers: Optional[list[Dict[str, str]]] = None
    Attachments: Optional[list[Dict[str, Any]]] = None


class PostmarkWebhookHandler(Controller):
    """Handle Postmark inbound email webhooks."""
    
    path = "/providers/postmark"
    
    @post("/inbound")
    async def handle_inbound(self, request: Request, data: PostmarkWebhookPayload) -> Response:
        """Handle Postmark inbound email webhook."""
        try:
            logger.info(f"Received Postmark webhook for message {data.MessageID}")
            
            # Initialize provider and protection for this request
            provider = PostmarkProvider()
            protection = EmailProtectionProcessor()
            
            # Convert to common EmailMessage format
            email_message = await provider.receive_message(data.model_dump())
            
            # Validate it's for our domain
            if not email_message.shield_address:
                return Response(
                    content={"error": "Not a cellophanemail.com address"},
                    status_code=HTTP_400_BAD_REQUEST
                )
            
            # TODO: In production, look up user by shield address
            # For now, use demo values
            user_email = "demo@example.com"
            user_id = "demo-user-001"
            organization_id = None
            
            # Process through email protection
            protection_result = await protection.process_email(
                email_message,
                user_email=user_email,
                organization_id=organization_id
            )
            
            # Build response based on protection decision
            response_data = {
                "status": "processed",
                "message_id": email_message.message_id,
                "shield_address": email_message.shield_address,
                "forwarded": protection_result.should_forward,
                "threat_level": protection_result.analysis.threat_level.value if protection_result.analysis else None,
                "toxicity_score": protection_result.analysis.toxicity_score if protection_result.analysis else 0.0,
                "block_reason": protection_result.block_reason,
                "processing_time_ms": protection_result.analysis.processing_time_ms if protection_result.analysis else 0
            }
            
            if protection_result.should_forward:
                logger.info(f"Email {email_message.message_id} forwarded to {user_email}")
                # TODO: Actually send the email via provider
            else:
                logger.info(f"Email {email_message.message_id} blocked: {protection_result.block_reason}")
            
            return Response(
                content=response_data,
                status_code=HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error processing Postmark webhook: {e}", exc_info=True)
            return Response(
                content={"error": str(e)},
                status_code=HTTP_400_BAD_REQUEST
            )