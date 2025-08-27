"""
PrivacyWebhookOrchestrator - Privacy-focused in-memory email processing.

REFACTOR PHASE: Now inherits from BaseWebhookOrchestrator for better structure.
This orchestrator coordinates in-memory email processing without database storage.
"""

import logging
from typing import Dict, Any

from .orchestrator_interface import BaseWebhookOrchestrator
from ...core.webhook_models import PostmarkWebhookPayload
from ..email_protection.memory_manager import MemoryManager
from ..email_protection.ephemeral_email import EphemeralEmail

logger = logging.getLogger(__name__)


class PrivacyWebhookOrchestrator(BaseWebhookOrchestrator):
    """
    Orchestrates webhook processing through privacy pipeline.
    
    GREEN PHASE: Minimal implementation to make tests pass.
    This will be refactored in later cycles.
    """
    
    def __init__(self):
        """Initialize with memory manager for in-memory processing."""
        self.memory_manager = MemoryManager()
    
    async def process_webhook(self, webhook_payload: PostmarkWebhookPayload) -> Dict[str, Any]:
        """
        Process webhook through privacy pipeline with in-memory storage.
        
        Returns 202 Accepted response for asynchronous processing.
        """
        logger.info(f"Processing webhook {webhook_payload.MessageID} through privacy pipeline")
        
        # Convert webhook to EphemeralEmail for memory storage
        ephemeral_email = EphemeralEmail(
            message_id=webhook_payload.MessageID,
            from_address=webhook_payload.From,
            to_addresses=[webhook_payload.To],
            subject=webhook_payload.Subject,
            text_body=webhook_payload.TextBody or "",
            html_body=webhook_payload.HtmlBody,
            user_email=webhook_payload.To,  # Shield address is user destination 
            ttl_seconds=300  # 5-minute TTL as per architecture
        )
        
        # Store in memory (not database)
        stored = self.memory_manager.store_email(ephemeral_email)
        
        if not stored:
            logger.warning(f"Failed to store email {webhook_payload.MessageID} - memory at capacity")
            return self._create_response(
                status="rejected",
                message_id=webhook_payload.MessageID,
                processing_type="privacy_pipeline_rejected",
                reason="memory_capacity_exceeded"
            )
        
        # Return 202 Accepted for async processing
        logger.info(f"Email {webhook_payload.MessageID} queued for async privacy processing")
        
        return self._create_response(
            status="accepted",
            message_id=webhook_payload.MessageID,
            processing_type="async_privacy_pipeline"
        )