"""Webhook endpoints for email processing - Refactored version."""

import logging
from typing import Dict, Any, Optional

from litestar import post, Request, Response
from litestar.controller import Controller
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from pydantic import BaseModel

from ..services.user_service import UserService
from ..core.email_processor import EmailProcessor
from ..core.email_message import EmailMessage
from ..services.webhook_handlers import PostmarkHandler

logger = logging.getLogger(__name__)


class WebhookController(Controller):
    """Handle inbound email webhooks from various providers."""
    
    path = "/webhooks"
    
    @post("/postmark")
    async def handle_postmark_inbound(
        self, 
        request: Request,
        data: Dict[str, Any]
    ) -> Response:
        """Handle Postmark inbound email webhook."""
        try:
            handler = PostmarkHandler()
            result = await handler.process_webhook(data)
            return self._build_response(result)
        except ValueError as e:
            return self._error_response(str(e), data.get("MessageID"), HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}", exc_info=True)
            return self._error_response("Internal error", data.get("MessageID"))
    
    def _build_response(self, result: Dict[str, Any]) -> Response:
        """Build HTTP response from processing result."""
        status_code = result.pop("status_code", HTTP_200_OK)
        return Response(content=result, status_code=status_code)
    
    def _error_response(self, error: str, message_id: str = "unknown", status: int = HTTP_400_BAD_REQUEST) -> Response:
        """Build error response."""
        return Response(
            content={"error": error, "message_id": message_id},
            status_code=status
        )


# Export router for app registration  
router = WebhookController