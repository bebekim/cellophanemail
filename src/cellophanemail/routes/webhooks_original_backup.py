"""Webhook endpoints for email processing."""

import logging
from datetime import datetime
from uuid import uuid4

from litestar import post, Request, Response
from litestar.controller import Controller
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from ..services.user_service import UserService
from ..core.email_processor import EmailProcessor
from ..core.email_message import EmailMessage

logger = logging.getLogger(__name__)


class PostmarkWebhookPayload(BaseModel):
    """Postmark inbound webhook payload structure."""
    
    From: str
    FromName: Optional[str] = None
    To: str
    ToFull: Optional[List[Dict[str, str]]] = None
    Subject: str
    MessageID: str
    Date: str
    TextBody: Optional[str] = None
    HtmlBody: Optional[str] = None
    Tag: Optional[str] = None
    Headers: Optional[List[Dict[str, str]]] = None
    Attachments: Optional[List[Dict[str, Any]]] = None


class WebhookController(Controller):
    """Handle inbound email webhooks from various providers."""
    
    path = "/webhooks"
    
    @post("/postmark")
    async def handle_postmark_inbound(
        self, 
        request: Request,
        data: PostmarkWebhookPayload
    ) -> Response:
        """Handle Postmark inbound email webhook with complete routing."""
        
        try:
            logger.info(f"Received Postmark webhook for message {data.MessageID}")
            
            # Step 1: Extract shield address from To field
            to_address = data.To.lower().strip()
            logger.info(f"Processing email to shield address: {to_address}")
            
            # Step 2: Validate domain
            if not to_address.endswith("@cellophanemail.com"):
                logger.warning(f"Invalid domain in To address: {to_address}")
                return Response(
                    content={"error": "Invalid domain", "message_id": data.MessageID},
                    status_code=HTTP_400_BAD_REQUEST
                )
            
            # Step 3: Lookup user by shield address
            user = await UserService.get_user_by_shield_address(to_address)
            if not user:
                logger.warning(f"No active user found for shield address: {to_address}")
                return Response(
                    content={"error": "Shield address not found", "message_id": data.MessageID},
                    status_code=HTTP_404_NOT_FOUND
                )
            
            # Handle dict vs object access for user
            user_id = user.get("id") if isinstance(user, dict) else user.id
            user_email = user.get("email") if isinstance(user, dict) else user.email
            user_org = user.get("organization") if isinstance(user, dict) else user.organization
            
            logger.info(f"Routing email to user {user_id} ({user_email})")
            
            # Step 4: Create EmailMessage object from Postmark webhook data
            email_message = EmailMessage.from_postmark_webhook(data.model_dump())
            
            # Set the processing context (user and organization)
            email_message.user_id = str(user_id)
            email_message.organization_id = str(user_org) if user_org else None
            
            # Override to_addresses to forward to real user email instead of shield
            email_message.to_addresses = [user_email]
            
            # Step 5: Process through Four Horsemen analysis
            processor = EmailProcessor()
            result = await processor.process(email_message)
            
            # Step 6: Return appropriate response
            if result.should_forward:
                logger.info(f"Email {data.MessageID} processed and forwarded to {user_email}")
                return Response(
                    content={
                        "status": "accepted",
                        "message_id": data.MessageID,
                        "processing": "forwarded",
                        "user_id": str(user_id),
                        "toxicity_score": result.toxicity_score,
                        "processing_time_ms": result.processing_time_ms
                    },
                    status_code=HTTP_200_OK
                )
            else:
                logger.info(f"Email {data.MessageID} blocked: {result.block_reason}")
                return Response(
                    content={
                        "status": "accepted",
                        "message_id": data.MessageID,
                        "processing": "blocked",
                        "user_id": str(user_id),
                        "block_reason": result.block_reason,
                        "toxicity_score": result.toxicity_score,
                        "horsemen_detected": result.horsemen_detected,
                        "processing_time_ms": result.processing_time_ms
                    },
                    status_code=HTTP_200_OK
                )
                
        except Exception as e:
            logger.error(f"Error processing Postmark webhook: {e}", exc_info=True)
            return Response(
                content={
                    "error": "Internal processing error",
                    "message_id": data.MessageID if data else "unknown"
                },
                status_code=HTTP_400_BAD_REQUEST
            )
    
    
    @post("/gmail")  
    async def handle_gmail_webhook(
        self,
        request: Request,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Handle Gmail API push notifications."""
        
        # TODO: Implement Gmail API webhook handling
        # TODO: Process via Gmail API plugin
        
        return {
            "status": "accepted",
            "notification": "processed"
        }
    
    @post("/test")
    async def test_webhook(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Test endpoint for webhook development."""
        
        return {
            "status": "received",
            "data_received": len(str(data)),
            "test": "successful"
        }


# Export router for app registration  
router = WebhookController