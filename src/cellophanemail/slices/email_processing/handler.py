"""Handler for Email Processing Vertical Slice.

TDD GREEN PHASE: Minimal implementation to pass failing tests.
"""

import logging
from datetime import datetime
from typing import Any

from .domain import ProcessEmailCommand, EmailProcessingResult
from .service import EmailProcessingService
from .models import EmailProcessingLog

logger = logging.getLogger(__name__)


class EmailProcessingHandler:
    """Entry point handler for Email Processing Vertical Slice.
    
    TDD: Created to satisfy test_email_processing_slice_handler_exists
    """
    
    def __init__(self):
        """Initialize the handler with its service."""
        self.service = EmailProcessingService()
    
    async def handle_email_processing(self, command: ProcessEmailCommand) -> EmailProcessingResult:
        """Handle email processing command.
        
        TDD: Minimal implementation to pass all failing tests.
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing email {command.email_message.id} through vertical slice")
            
            # Step 1: Check organization limits
            can_process = await self.service.check_organization_limits(command.organization_id)
            if not can_process:
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                return EmailProcessingResult(
                    email_id=command.email_message.id,
                    should_forward=False,
                    block_reason="Organization email limit exceeded",
                    processing_time_ms=processing_time
                )
            
            # Step 2: Analyze email content
            analysis_result = await self.service.analyze_email_content(command.email_message)
            
            # Step 3: Create processing result
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = EmailProcessingResult(
                email_id=command.email_message.id,
                should_forward=analysis_result['should_forward'],
                block_reason=analysis_result['block_reason'],
                toxicity_score=analysis_result['toxicity_score'],
                horsemen_detected=analysis_result['horsemen_detected'],
                ai_analysis={
                    'classification': analysis_result['classification'],
                    'reasoning': analysis_result['reasoning'],
                    'specific_examples': analysis_result['specific_examples'],
                    'confidence_score': analysis_result['confidence_score']
                },
                processing_time_ms=processing_time
            )
            
            # Step 4: Log the processing (slice-specific logging)
            await self._log_processing(command, result)
            
            # Step 5: Forward email if approved
            if result.should_forward:
                await self.service.forward_email(command.email_message)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing email {command.email_message.id}: {e}", exc_info=True)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return EmailProcessingResult(
                email_id=command.email_message.id,
                should_forward=False,
                block_reason=f"Processing error: {str(e)}",
                processing_time_ms=processing_time
            )
    
    async def _log_processing(self, command: ProcessEmailCommand, result: EmailProcessingResult):
        """Log the email processing using slice-specific model.
        
        TDD: Satisfies test_slice_logs_to_its_own_model
        """
        log_entry = EmailProcessingLog(
            organization_id=command.organization_id,
            user_id=command.user_id,
            email_id=command.email_message.id,
            from_address=command.email_message.from_address,
            to_addresses=command.email_message.to_addresses,
            subject=command.email_message.subject,
            status="forwarded" if result.should_forward else "blocked",
            toxicity_score=result.toxicity_score,
            horsemen_detected=result.horsemen_detected,
            processing_time_ms=result.processing_time_ms
        )
        
        await log_entry.save()