"""Webhook endpoints for email processing - Single file refactored version."""

import logging
import os
from typing import Dict, Any, List, Optional

from litestar import post, Request, Response
from litestar.controller import Controller
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from pydantic import BaseModel

from ..core.email_message import EmailMessage
from ..core.webhook_models import PostmarkWebhookPayload

# Use new provider/feature architecture (legacy support removed)
from ..providers.postmark.provider import PostmarkProvider
from ..features.email_protection import EmailProtectionProcessor
from ..features.shield_addresses import ShieldAddressManager
from ..features.privacy_integration.privacy_webhook_orchestrator import PrivacyWebhookOrchestrator
from ..features.email_processing_strategy import ProcessingStrategyManager

logger = logging.getLogger(__name__)
logger.info("Using new provider/feature architecture for email processing")


class WebhookController(Controller):
    """Handle inbound email webhooks from various providers with privacy mode support."""
    
    path = "/webhooks"
    
    def __init__(self, owner):
        """Initialize controller with processing strategy manager."""
        super().__init__(owner)
        self.strategy_manager = ProcessingStrategyManager()
    
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
            
            # Use strategy manager for processing (privacy mode aware)
            processing_result = await self.strategy_manager.process_email(data, user)
            
            return Response(
                content=processing_result.response_data,
                status_code=processing_result.status_code
            )
            
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
        """Lookup user by shield address using new architecture."""
        # Use new shield address manager
        shield_manager = ShieldAddressManager()
        shield_info = await shield_manager.lookup_user_by_shield_address(shield_address)
        if not shield_info:
            logger.warning(f"No active user found for shield address: {shield_address}")
            raise ValueError(self._error_response("Shield address not found", message_id, HTTP_404_NOT_FOUND))
        
        # Convert to legacy format for compatibility
        return {
            "id": shield_info.user_id,
            "email": shield_info.user_email,
            "organization": shield_info.organization_id
        }
    
    
    def _get_user_field(self, user: Any, field: str) -> Optional[str]:
        """Safely extract field from user (handles dict or object)."""
        return user.get(field) if isinstance(user, dict) else getattr(user, field, None)
    
    
    
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