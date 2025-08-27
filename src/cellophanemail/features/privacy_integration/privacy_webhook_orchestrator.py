"""
PrivacyWebhookOrchestrator - Minimal implementation for TDD CYCLE 1 GREEN phase.

This orchestrator coordinates in-memory email processing without database storage.
"""

import logging
from typing import Dict, Any

from ...core.webhook_models import PostmarkWebhookPayload
from ..email_protection.memory_manager import MemoryManager
from ..email_protection.ephemeral_email import EphemeralEmail

logger = logging.getLogger(__name__)


class PrivacyWebhookOrchestrator:
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
            return {
                "status": "rejected",
                "message_id": webhook_payload.MessageID,
                "reason": "memory_capacity_exceeded"
            }
        
        # Return 202 Accepted for async processing
        logger.info(f"Email {webhook_payload.MessageID} queued for async privacy processing")
        
        return {
            "status": "accepted",
            "message_id": webhook_payload.MessageID,
            "processing": "async_privacy_pipeline"
        }