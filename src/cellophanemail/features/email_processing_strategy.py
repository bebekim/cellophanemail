"""
Email Processing Manager - Privacy-only email processing pipeline.

This module implements privacy-focused in-memory processing where email content
is NEVER stored in any database, ensuring complete user privacy.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any

from ..core.webhook_models import PostmarkWebhookPayload
from .privacy_integration.privacy_webhook_orchestrator import PrivacyWebhookOrchestrator

logger = logging.getLogger(__name__)


@dataclass  
class ProcessingResult:
    """Result from privacy processing."""
    status_code: int
    response_data: Dict[str, Any]


class ProcessingStrategyManager:
    """Manages privacy-only email processing."""
    
    def __init__(self):
        """Initialize with privacy-only processing."""
        self.orchestrator = PrivacyWebhookOrchestrator()
        logger.info("Email processing initialized with privacy-only mode (no content storage)")
    
    async def process_email(
        self, 
        webhook_payload: PostmarkWebhookPayload,
        user_context: Dict[str, Any]
    ) -> ProcessingResult:
        """
        Process email through privacy pipeline with zero persistence.
        
        Args:
            webhook_payload: Inbound email data from webhook
            user_context: User and organization information
            
        Returns:
            ProcessingResult with status code and response data
        """
        try:
            logger.info(f"Processing email {webhook_payload.MessageID} through privacy pipeline")
            
            response_data = await self.orchestrator.process_webhook(webhook_payload)
            
            # Privacy pipeline returns 202 Accepted for async processing
            return ProcessingResult(
                status_code=202,
                response_data=response_data
            )
            
        except Exception as e:
            logger.error(f"Error in privacy processing: {e}", exc_info=True)
            
            return ProcessingResult(
                status_code=503,
                response_data={
                    "error": "Privacy processing unavailable",
                    "message_id": webhook_payload.MessageID
                }
            )