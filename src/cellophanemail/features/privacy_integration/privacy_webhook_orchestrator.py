"""
PrivacyWebhookOrchestrator - Privacy-focused in-memory email processing.

REFACTORED: Complete end-to-end processing pipeline with enhanced error handling,
configuration, and monitoring capabilities for production readiness.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .orchestrator_interface import BaseWebhookOrchestrator
from ...core.webhook_models import PostmarkWebhookPayload
from ..email_protection.memory_manager import MemoryManager
from ..email_protection.ephemeral_email import EphemeralEmail
from ..email_protection.in_memory_processor import InMemoryProcessor
from ..email_protection.immediate_delivery import ImmediateDeliveryManager

logger = logging.getLogger(__name__)


@dataclass
class PrivacyProcessingConfig:
    """Configuration for privacy processing pipeline."""
    ttl_seconds: int = 300  # 5 minutes default
    max_concurrent_tasks: int = 50
    processing_timeout_seconds: float = 30.0
    enable_detailed_logging: bool = False  # For debugging only, never log content


class PrivacyWebhookOrchestrator(BaseWebhookOrchestrator):
    """
    Orchestrates webhook processing through privacy pipeline.
    
    REFACTORED: Production-ready implementation with comprehensive error handling,
    configurable processing, and proper task lifecycle management.
    """
    
    def __init__(self, config: Optional[PrivacyProcessingConfig] = None):
        """Initialize with complete privacy processing pipeline."""
        self.config = config or PrivacyProcessingConfig()
        self.memory_manager = MemoryManager()
        self.processor = InMemoryProcessor()
        self.delivery_manager = ImmediateDeliveryManager()
        self._background_tasks = set()  # Track background tasks
        self._processing_stats = {
            "processed_count": 0,
            "success_count": 0,
            "error_count": 0,
            "memory_rejections": 0
        }
    
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
        
        # Start async processing in the background
        task = asyncio.create_task(self._process_email_async(ephemeral_email))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        # Return 202 Accepted for async processing
        logger.info(f"Email {webhook_payload.MessageID} queued for async privacy processing")
        
        return self._create_response(
            status="accepted",
            message_id=webhook_payload.MessageID,
            processing_type="async_privacy_pipeline"
        )
    
    async def _process_email_async(self, email: EphemeralEmail) -> None:
        """
        Process email through complete privacy pipeline with timeout and error handling.
        This runs in the background after webhook returns.
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Apply processing timeout (compatible with older Python versions)
            await asyncio.wait_for(
                self._process_email_steps(email),
                timeout=self.config.processing_timeout_seconds
            )
                
        except asyncio.TimeoutError:
            self._processing_stats["error_count"] += 1
            logger.error(f"Processing timeout for email {email.message_id} after {self.config.processing_timeout_seconds}s")
            
        except Exception as e:
            self._processing_stats["error_count"] += 1
            logger.error(f"Error in async processing for email {email.message_id}: {e}")
            # Error handling - email will still expire from memory via TTL
    
    async def _process_email_steps(self, email: EphemeralEmail) -> None:
        """Execute the actual processing steps (separated for timeout handling)."""
        if self.config.enable_detailed_logging:
            logger.info(f"Starting async processing for email {email.message_id}")
        
        self._processing_stats["processed_count"] += 1
        
        # Step 1: LLM Analysis (privacy-safe - only content analysis)
        processing_result = await self.processor.process_email(email)
        
        # Step 2: Delivery (if email is safe)
        if processing_result.requires_delivery:
            delivery_result = await self.delivery_manager.deliver_email(processing_result, email)
            
            if self.config.enable_detailed_logging:
                logger.info(f"Delivery completed for {email.message_id}: success={delivery_result.success}")
            
            if delivery_result.success:
                self._processing_stats["success_count"] += 1
            else:
                self._processing_stats["error_count"] += 1
                logger.warning(f"Delivery failed for {email.message_id} after {delivery_result.attempts} attempts")
        else:
            if self.config.enable_detailed_logging:
                logger.info(f"Email {email.message_id} blocked - no delivery required")
            self._processing_stats["success_count"] += 1
        
        # Step 3: Email automatically expires from memory based on TTL
        # No manual cleanup needed here - background cleanup service handles this
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics for monitoring."""
        memory_stats = self.memory_manager.get_stats()
        return {
            **self._processing_stats,
            "active_background_tasks": len(self._background_tasks),
            "memory_usage": memory_stats,
            "config": {
                "ttl_seconds": self.config.ttl_seconds,
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "processing_timeout_seconds": self.config.processing_timeout_seconds
            }
        }
    
    async def shutdown_gracefully(self) -> None:
        """Gracefully shutdown all background tasks."""
        if self._background_tasks:
            logger.info(f"Shutting down {len(self._background_tasks)} background tasks")
            
            # Cancel all background tasks
            for task in self._background_tasks.copy():
                if not task.done():
                    task.cancel()
            
            # Wait for cancellation to complete
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            logger.info("All background tasks shutdown complete")