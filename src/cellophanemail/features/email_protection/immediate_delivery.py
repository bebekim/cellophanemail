"""ImmediateDeliveryManager for instant email delivery with retry logic."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from .ephemeral_email import EphemeralEmail
from .in_memory_processor import ProcessingResult
from .contracts import DeliveryManagerInterface

logger = logging.getLogger(__name__)


@dataclass
class DeliveryResult:
    """
    Result of email delivery attempt.
    """
    success: bool
    attempts: int
    error_message: Optional[str] = None
    delivery_time_ms: Optional[int] = None


class ImmediateDeliveryManager(DeliveryManagerInterface):
    """
    Manages immediate delivery of processed emails with retry logic.
    
    Provides reliable email delivery with automatic retries, exponential backoff,
    and comprehensive error handling for in-memory email processing pipeline.
    """
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize ImmediateDeliveryManager.
        
        Args:
            max_retries: Maximum number of delivery attempts (default: 3)
        """
        self.max_retries = max_retries
        
    async def deliver_email(self, processing_result: ProcessingResult, email: EphemeralEmail) -> DeliveryResult:
        """
        Deliver a processed email with retry logic.
        
        Args:
            processing_result: Result from email processing containing delivery info
            email: Original ephemeral email with metadata
            
        Returns:
            DeliveryResult with success status and attempt details
        """
        logger.info(f"Starting delivery for email {email.message_id}")
        
        # Skip delivery if not required
        if not processing_result.requires_delivery:
            logger.info(f"Email {email.message_id} does not require delivery")
            return DeliveryResult(
                success=True,
                attempts=0,
                error_message="No delivery required"
            )
        
        # Attempt delivery with retries
        attempts = 0
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            attempts = attempt
            
            try:
                success = await self._attempt_delivery(processing_result, email)
                
                if success:
                    logger.info(f"Email {email.message_id} delivered successfully on attempt {attempt}")
                    return DeliveryResult(
                        success=True,
                        attempts=attempts,
                        delivery_time_ms=100 * attempt  # Simulated delivery time
                    )
                else:
                    last_error = f"Delivery failed on attempt {attempt}"
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Delivery attempt {attempt} failed for {email.message_id}: {last_error}")
            
            # Exponential backoff (except on last attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(0.1 * (2 ** attempt))  # 0.2s, 0.4s, 0.8s
        
        # All attempts failed
        logger.error(f"All delivery attempts failed for email {email.message_id}: {last_error}")
        return DeliveryResult(
            success=False,
            attempts=attempts,
            error_message=last_error
        )
    
    async def _attempt_delivery(self, processing_result: ProcessingResult, email: EphemeralEmail) -> bool:
        """
        Attempt to deliver an email once.
        
        This is a minimal implementation for testing. In production, this would
        integrate with the actual email delivery system (Postmark/SMTP).
        
        Args:
            processing_result: Processing result with delivery targets
            email: Email to deliver
            
        Returns:
            bool: True if delivery successful, False otherwise
        """
        # Simulate delivery logic
        # In production: use EmailSenderFactory to get sender and send email
        
        if not processing_result.delivery_targets:
            raise ValueError("No delivery targets specified")
        
        # Simulate successful delivery for clean emails
        if processing_result.action.value == 'forward_clean':
            return True
        
        # Simulate occasional failures for other types (for retry testing)
        import random
        return random.random() > 0.1  # 90% success rate