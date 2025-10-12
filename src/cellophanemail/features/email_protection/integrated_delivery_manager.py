"""
IntegratedDeliveryManager for connecting privacy pipeline to real email delivery.

Bridges the gap between ProcessingResult and actual email sending through
EmailSenderFactory while maintaining privacy principles and transparency.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

from .ephemeral_email import EphemeralEmail
from .in_memory_processor import ProcessingResult, ProtectionAction
from .email_composition_strategy import (
    EmailCompositionStrategy, 
    DeliveryConfiguration, 
    EmailComposition
)
from .contracts import DeliveryManagerInterface
from ...core.email_delivery.factory import EmailSenderFactory
from ...core.email_delivery.base import BaseEmailSender

logger = logging.getLogger(__name__)


@dataclass
class EnhancedDeliveryResult:
    """
    Extended delivery result with protection context.
    """
    success: bool
    attempts: int
    protection_action: ProtectionAction
    toxicity_score: float
    error_message: Optional[str] = None
    delivery_time_ms: Optional[int] = None
    email_sender_used: Optional[str] = None


class IntegratedDeliveryManager(DeliveryManagerInterface):
    """
    Integrated delivery manager connecting privacy processing results 
    with the actual email delivery system (Postmark/SMTP).
    
    Purpose: Bridge the gap between ProcessingResult and BaseEmailSender
    by composing appropriate emails based on protection actions and 
    delivering them through the configured email sender.
    """
    
    def __init__(self, delivery_config: DeliveryConfiguration):
        """
        Initialize integrated delivery manager.
        
        Args:
            delivery_config: Configuration for email delivery integration
            
        Raises:
            ValueError: If delivery configuration is invalid
        """
        self.config = delivery_config
        self.max_retries = delivery_config.max_retries
        
        # Initialize email sender through factory
        try:
            self.email_sender: BaseEmailSender = EmailSenderFactory.create_sender(
                sender_type=delivery_config.sender_type,
                config=delivery_config.config
            )
        except ValueError as e:
            raise ValueError(f"Invalid delivery configuration: {e}")
        
        # Initialize email composition strategy
        self.composer = EmailCompositionStrategy()
        
        logger.info(f"IntegratedDeliveryManager initialized with {delivery_config.sender_type} sender")
        
    async def deliver_email(self, processing_result: ProcessingResult, email: EphemeralEmail) -> EnhancedDeliveryResult:
        """
        Deliver processed email through integrated delivery system.
        
        Args:
            processing_result: Result from email processing containing delivery info
            email: Original ephemeral email with metadata
            
        Returns:
            EnhancedDeliveryResult with detailed delivery information
        """
        start_time = time.time()
        
        logger.info(f"Starting integrated delivery for email {email.message_id}")
        
        # Skip delivery if not required (e.g., blocked emails)
        if not processing_result.requires_delivery:
            logger.info(f"Email {email.message_id} does not require delivery ({processing_result.action.value})")
            return EnhancedDeliveryResult(
                success=True,
                attempts=0,
                protection_action=processing_result.action,
                toxicity_score=processing_result.toxicity_score,
                error_message="No delivery required",
                email_sender_used=self.config.sender_type
            )
        
        # Compose email using strategy pattern
        try:
            composition = self.composer.compose_email(processing_result, email, self.config)
        except Exception as e:
            logger.error(f"Email composition failed for {email.message_id}: {e}")
            return EnhancedDeliveryResult(
                success=False,
                attempts=0,
                protection_action=processing_result.action,
                toxicity_score=processing_result.toxicity_score,
                error_message=f"Email composition failed: {str(e)}",
                email_sender_used=self.config.sender_type
            )
        
        # Attempt delivery with retry logic
        attempts = 0
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            attempts = attempt
            
            try:
                success = await self._attempt_delivery(composition, processing_result.delivery_targets[0])
                
                if success:
                    delivery_time = int((time.time() - start_time) * 1000)
                    logger.info(f"Email {email.message_id} delivered successfully on attempt {attempt}")
                    return EnhancedDeliveryResult(
                        success=True,
                        attempts=attempts,
                        protection_action=processing_result.action,
                        toxicity_score=processing_result.toxicity_score,
                        delivery_time_ms=delivery_time,
                        email_sender_used=self.config.sender_type
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
        return EnhancedDeliveryResult(
            success=False,
            attempts=attempts,
            protection_action=processing_result.action,
            toxicity_score=processing_result.toxicity_score,
            error_message=last_error,
            email_sender_used=self.config.sender_type
        )
    
    async def _attempt_delivery(self, composition: EmailComposition, to_address: str) -> bool:
        """
        Attempt to deliver an email once using the configured email sender.
        
        Args:
            composition: Composed email ready for delivery
            to_address: Target email address
            
        Returns:
            bool: True if delivery successful, False otherwise
        """
        try:
            # Use the real email sender through existing factory
            success = await self.email_sender.send_email(
                to_address=to_address,
                subject=composition.subject,
                content=composition.body,
                headers=composition.headers
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Email sender error: {e}")
            return False