"""Adapter to integrate the email processing vertical slice with existing infrastructure."""

import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass

from ..core.email_message import EmailMessage
from ..slices.email_processing.handler import EmailProcessingHandler
from ..slices.email_processing.domain import ProcessEmailCommand

logger = logging.getLogger(__name__)


@dataclass
class LegacyProcessingResult:
    """Result format compatible with existing webhook expectations."""
    should_forward: bool
    toxicity_score: float
    processing_time_ms: int
    block_reason: Optional[str] = None
    horsemen_detected: Optional[list] = None


class EmailProcessingAdapter:
    """Adapts between legacy EmailProcessor interface and new vertical slice."""
    
    def __init__(self):
        self.handler = EmailProcessingHandler()
        logger.info("EmailProcessingAdapter initialized with vertical slice handler")
    
    async def process(self, email_message: EmailMessage) -> LegacyProcessingResult:
        """
        Process email using vertical slice while maintaining legacy interface.
        
        This adapter allows gradual migration by maintaining the existing 
        EmailProcessor interface while using the new vertical slice internally.
        """
        try:
            # Convert EmailMessage to slice command
            command = ProcessEmailCommand(
                message_id=email_message.message_id,
                from_address=email_message.from_address,
                to_addresses=email_message.to_addresses,
                subject=email_message.subject,
                text_body=email_message.text_body,
                html_body=email_message.html_body,
                user_id=email_message.user_id,
                organization_id=email_message.organization_id,
                headers=email_message.headers,
                attachments=email_message.attachments
            )
            
            logger.info(f"Processing email {command.message_id} through vertical slice")
            
            # Process through vertical slice
            result = await self.handler.process_email(command)
            
            # Convert slice result to legacy format
            legacy_result = LegacyProcessingResult(
                should_forward=result.should_forward,
                toxicity_score=result.analysis.toxicity_score if result.analysis else 0.0,
                processing_time_ms=result.processing_time_ms,
                block_reason=result.block_reason,
                horsemen_detected=result.analysis.horsemen_detected if result.analysis else []
            )
            
            logger.info(
                f"Email {command.message_id} processed: "
                f"forward={legacy_result.should_forward}, "
                f"toxicity={legacy_result.toxicity_score:.2f}"
            )
            
            return legacy_result
            
        except Exception as e:
            logger.error(f"Error in EmailProcessingAdapter: {e}", exc_info=True)
            # Return safe default that blocks the email
            return LegacyProcessingResult(
                should_forward=False,
                toxicity_score=1.0,
                processing_time_ms=0,
                block_reason=f"Processing error: {str(e)}",
                horsemen_detected=["error"]
            )


# Singleton instance for easy drop-in replacement
email_processing_adapter = EmailProcessingAdapter()