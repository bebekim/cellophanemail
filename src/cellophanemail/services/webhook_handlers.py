"""Webhook processing handlers for different email providers."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from pydantic import BaseModel, ValidationError
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from ..services.user_service import UserService
from ..core.email_processor import EmailProcessor
from ..core.email_message import EmailMessage

logger = logging.getLogger(__name__)


class PostmarkWebhookPayload(BaseModel):
    """Postmark inbound webhook payload structure."""
    From: str
    To: str
    Subject: str
    MessageID: str
    Date: str
    FromName: Optional[str] = None
    ToFull: Optional[list] = None
    TextBody: Optional[str] = None
    HtmlBody: Optional[str] = None
    Headers: Optional[list] = None
    Attachments: Optional[list] = None


class PostmarkHandler:
    """Handle Postmark webhook processing with small, focused methods."""
    
    def __init__(self):
        self.user_service = UserService()
        self.email_processor = EmailProcessor()
    
    async def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for processing Postmark webhook."""
        payload = self._validate_payload(data)
        shield_address = self._extract_shield_address(payload)
        self._validate_domain(shield_address)
        
        user = await self._get_user(shield_address)
        email_message = self._create_email_message(payload, user)
        result = await self._process_email(email_message)
        
        return self._format_response(result, payload.MessageID, user)
    
    def _validate_payload(self, data: Dict[str, Any]) -> PostmarkWebhookPayload:
        """Validate and parse the webhook payload."""
        try:
            return PostmarkWebhookPayload(**data)
        except ValidationError as e:
            logger.error(f"Invalid Postmark payload: {e}")
            raise ValueError("Invalid webhook payload")
    
    def _extract_shield_address(self, payload: PostmarkWebhookPayload) -> str:
        """Extract and normalize the shield address."""
        shield = payload.To.lower().strip()
        logger.info(f"Processing email to: {shield}")
        return shield
    
    def _validate_domain(self, address: str) -> None:
        """Ensure email is sent to our domain."""
        if not address.endswith("@cellophanemail.com"):
            logger.warning(f"Invalid domain: {address}")
            raise ValueError("Invalid domain")
    
    async def _get_user(self, shield_address: str) -> Dict[str, Any]:
        """Lookup user by shield address."""
        user = await self.user_service.get_user_by_shield_address(shield_address)
        if not user:
            logger.warning(f"Shield not found: {shield_address}")
            raise ValueError("Shield address not found")
        return user
    
    def _create_email_message(self, payload: PostmarkWebhookPayload, user: Dict[str, Any]) -> EmailMessage:
        """Create EmailMessage from payload and user context."""
        email = EmailMessage.from_postmark_webhook(payload.model_dump())
        email.user_id = self._get_user_field(user, "id")
        email.organization_id = self._get_user_field(user, "organization")
        email.to_addresses = [self._get_user_field(user, "email")]
        return email
    
    def _get_user_field(self, user: Any, field: str) -> Optional[str]:
        """Safely extract field from user (handles dict or object)."""
        value = user.get(field) if isinstance(user, dict) else getattr(user, field, None)
        return str(value) if value else None
    
    async def _process_email(self, email_message: EmailMessage) -> Any:
        """Process email through AI analysis pipeline."""
        return await self.email_processor.process(email_message)
    
    def _format_response(self, result: Any, message_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
        """Format the processing result for response."""
        base_response = {
            "status": "accepted",
            "message_id": message_id,
            "user_id": self._get_user_field(user, "id"),
            "toxicity_score": result.toxicity_score,
            "processing_time_ms": result.processing_time_ms
        }
        
        if result.should_forward:
            return self._format_forward_response(base_response)
        else:
            return self._format_block_response(base_response, result)
    
    def _format_forward_response(self, base: Dict[str, Any]) -> Dict[str, Any]:
        """Format response for forwarded email."""
        base["processing"] = "forwarded"
        base["status_code"] = HTTP_200_OK
        logger.info(f"Email {base['message_id']} forwarded")
        return base
    
    def _format_block_response(self, base: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """Format response for blocked email."""
        base["processing"] = "blocked"
        base["block_reason"] = result.block_reason
        base["horsemen_detected"] = result.horsemen_detected
        base["status_code"] = HTTP_200_OK
        logger.info(f"Email {base['message_id']} blocked: {result.block_reason}")
        return base