"""Postmark webhook handler."""

import logging
from typing import Dict, Any, Optional

from litestar import post, Response, Request
from litestar.controller import Controller
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from pydantic import BaseModel, ValidationError

from .provider import PostmarkProvider
from ..contracts import EmailMessage
from ...features.email_protection import EmailProtectionProcessor
from ...features.shield_addresses import ShieldAddressManager

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
    async def handle_inbound(self, request: Request, data: Dict[str, Any]) -> Response:
        """Handle Postmark inbound email webhook."""
        try:
            # First, validate the incoming data structure
            try:
                webhook_data = PostmarkWebhookPayload.model_validate(data)
                logger.info(f"Received valid Postmark webhook for message {webhook_data.MessageID}")
            except ValidationError as e:
                # Log client info for monitoring/rate limiting
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("user-agent", "unknown")
                logger.warning(f"Invalid webhook payload from {client_ip} (UA: {user_agent[:50]}): {e}")
                logger.debug(f"Payload received: {data}")
                
                # Handle common invalid cases gracefully
                if not data or data == {}:
                    # Empty request - likely health check, bot, or scanner
                    logger.info(f"Empty webhook request from {client_ip} - possible health check or scanner")
                    return Response(
                        content={
                            "status": "invalid", 
                            "error": "Empty payload - expecting Postmark webhook data",
                            "hint": "Use POST /providers/postmark/health for health checks"
                        },
                        status_code=HTTP_400_BAD_REQUEST
                    )
                
                # Missing required fields
                missing_fields = []
                required_fields = ["From", "To", "Subject", "MessageID", "Date"]
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                return Response(
                    content={
                        "status": "invalid",
                        "error": f"Missing required fields: {', '.join(missing_fields)}",
                        "expected": "Valid Postmark inbound webhook payload"
                    },
                    status_code=HTTP_400_BAD_REQUEST
                )
            
            # Initialize provider, protection, and shield address manager for this request
            provider = PostmarkProvider()
            protection = EmailProtectionProcessor()
            shield_manager = ShieldAddressManager()
            
            # Convert to common EmailMessage format
            email_message = await provider.receive_message(webhook_data.model_dump())
            
            # Validate it's for our domain
            if not email_message.shield_address:
                return Response(
                    content={"error": "Not a cellophanemail.com address"},
                    status_code=HTTP_400_BAD_REQUEST
                )
            
            # Look up user by shield address
            shield_info = await shield_manager.lookup_user_by_shield_address(email_message.shield_address)
            if not shield_info:
                logger.warning(f"No active user found for shield address: {email_message.shield_address}")
                return Response(
                    content={"error": "Shield address not found or inactive"},
                    status_code=HTTP_404_NOT_FOUND
                )
            
            user_email = shield_info.user_email
            user_id = shield_info.user_id
            organization_id = shield_info.organization_id
            
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
    
    @post("/health")
    async def health_check(self, request: Request) -> Response:
        """Health check endpoint for monitoring."""
        return Response(
            content={
                "status": "healthy",
                "service": "postmark-webhook",
                "endpoint": "/providers/postmark/inbound"
            },
            status_code=HTTP_200_OK
        )