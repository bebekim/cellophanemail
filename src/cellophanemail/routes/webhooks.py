"""Webhook endpoints for email processing - Single file refactored version."""

import logging
import os
from typing import Dict, Any, List, Optional

from litestar import post, Request, Response
from litestar.controller import Controller
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from pydantic import BaseModel

from ..services.user_service import UserService
from ..core.email_processor import EmailProcessor
from ..core.email_message import EmailMessage

# Feature flag for vertical slice architecture migration
USE_VERTICAL_SLICE = os.getenv("USE_VERTICAL_SLICE", "true").lower() == "true"

if USE_VERTICAL_SLICE:
    from ..adapters.email_processing_adapter import email_processing_adapter
    logger = logging.getLogger(__name__)
    logger.info("Using Vertical Slice Architecture for email processing")
else:
    logger = logging.getLogger(__name__)
    logger.info("Using traditional layered architecture for email processing")


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
        """Handle Postmark inbound email webhook - orchestrates the flow."""
        try:
            logger.info(f"Received Postmark webhook for message {data.MessageID}")
            
            to_address = self._extract_shield_address(data)
            self._validate_domain(to_address, data.MessageID)
            user = await self._get_user(to_address, data.MessageID)
            email_message = self._prepare_email(data, user)
            result = await self._process_email(email_message)
            
            return self._build_response(result, data.MessageID, user)
            
        except ValueError as e:
            return e.args[0]  # Already a formatted Response
        except Exception as e:
            logger.error(f"Error processing Postmark webhook: {e}", exc_info=True)
            return self._error_response("Internal processing error", data.MessageID)
    
    def _extract_shield_address(self, data: PostmarkWebhookPayload) -> str:
        """Extract and normalize shield address from To field."""
        address = data.To.lower().strip()
        logger.info(f"Processing email to shield address: {address}")
        return address
    
    def _validate_domain(self, address: str, message_id: str) -> None:
        """Validate that email is sent to our domain."""
        if not address.endswith("@cellophanemail.com"):
            logger.warning(f"Invalid domain in To address: {address}")
            raise ValueError(self._error_response("Invalid domain", message_id, HTTP_400_BAD_REQUEST))
    
    async def _get_user(self, shield_address: str, message_id: str) -> Dict[str, Any]:
        """Lookup user by shield address."""
        user = await UserService.get_user_by_shield_address(shield_address)
        if not user:
            logger.warning(f"No active user found for shield address: {shield_address}")
            raise ValueError(self._error_response("Shield address not found", message_id, HTTP_404_NOT_FOUND))
        return user
    
    def _prepare_email(self, data: PostmarkWebhookPayload, user: Dict[str, Any]) -> EmailMessage:
        """Create EmailMessage with user context."""
        email_message = EmailMessage.from_postmark_webhook(data.model_dump())
        
        user_id = self._get_user_field(user, "id")
        user_email = self._get_user_field(user, "email")
        user_org = self._get_user_field(user, "organization")
        
        logger.info(f"Routing email to user {user_id} ({user_email})")
        
        email_message.user_id = str(user_id)
        email_message.organization_id = str(user_org) if user_org else None
        email_message.to_addresses = [user_email]
        
        return email_message
    
    def _get_user_field(self, user: Any, field: str) -> Optional[str]:
        """Safely extract field from user (handles dict or object)."""
        return user.get(field) if isinstance(user, dict) else getattr(user, field, None)
    
    async def _process_email(self, email_message: EmailMessage) -> Any:
        """Process email through Four Horsemen AI analysis."""
        if USE_VERTICAL_SLICE:
            logger.info(f"Processing email {email_message.message_id} via vertical slice")
            return await email_processing_adapter.process(email_message)
        else:
            processor = EmailProcessor()
            return await processor.process(email_message)
    
    def _build_response(self, result: Any, message_id: str, user: Dict[str, Any]) -> Response:
        """Build response based on processing result."""
        user_id = str(self._get_user_field(user, "id"))
        
        base_response = {
            "status": "accepted",
            "message_id": message_id,
            "user_id": user_id,
            "toxicity_score": result.toxicity_score,
            "processing_time_ms": result.processing_time_ms
        }
        
        if result.should_forward:
            return self._forward_response(base_response, user)
        else:
            return self._block_response(base_response, result)
    
    def _forward_response(self, base: Dict[str, Any], user: Dict[str, Any]) -> Response:
        """Build response for forwarded email."""
        user_email = self._get_user_field(user, "email")
        logger.info(f"Email {base['message_id']} processed and forwarded to {user_email}")
        
        base["processing"] = "forwarded"
        return Response(content=base, status_code=HTTP_200_OK)
    
    def _block_response(self, base: Dict[str, Any], result: Any) -> Response:
        """Build response for blocked email."""
        logger.info(f"Email {base['message_id']} blocked: {result.block_reason}")
        
        base.update({
            "processing": "blocked",
            "block_reason": result.block_reason,
            "horsemen_detected": result.horsemen_detected
        })
        return Response(content=base, status_code=HTTP_200_OK)
    
    def _error_response(self, error: str, message_id: str, status: int = HTTP_400_BAD_REQUEST) -> Response:
        """Build error response."""
        return Response(
            content={"error": error, "message_id": message_id},
            status_code=status
        )
    
    @post("/gmail")  
    async def handle_gmail_webhook(
        self,
        request: Request,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Handle Gmail API push notifications."""
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