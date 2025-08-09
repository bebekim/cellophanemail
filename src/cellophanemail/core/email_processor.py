"""Email processing pipeline with Four Horsemen analysis."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from .email_message import EmailMessage
from .content_processor import ContentProcessor, ProcessingContext, EmailProcessingResult
from .email_delivery import EmailSenderFactory
from ..models.email_log import EmailLog
from ..models.organization import Organization
from ..models.user import User

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of email processing."""
    email_id: UUID
    should_forward: bool
    block_reason: Optional[str] = None
    toxicity_score: float = 0.0
    horsemen_detected: List[str] = None
    ai_analysis: Dict[str, Any] = None
    processing_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.horsemen_detected is None:
            self.horsemen_detected = []
        if self.ai_analysis is None:
            self.ai_analysis = {}


class EmailProcessor:
    """Main email processing pipeline."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the email processor."""
        self.content_processor = ContentProcessor()
        self.config = config or {}
        
        # Initialize email sender if configuration is provided
        self.email_sender = None
        if self.config:
            sender_type = self.config.get('EMAIL_DELIVERY_METHOD', 'smtp')
            try:
                self.email_sender = EmailSenderFactory.create_sender(sender_type, self.config)
                logger.info(f"Initialized {sender_type} email sender")
            except Exception as e:
                logger.warning(f"Failed to initialize email sender: {e}. Email forwarding will be disabled.")
        
    async def process(self, email_message: EmailMessage) -> ProcessingResult:
        """Process an email through the Four Horsemen analysis pipeline."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing email {email_message.id} from {email_message.from_address}")
            
            # Step 1: Identify organization/user context
            org_id, user_id = await self._identify_context(email_message)
            email_message.organization_id = org_id
            email_message.user_id = user_id
            
            # Step 2: Check organization limits and status
            if org_id:
                can_process = await self._check_organization_limits(org_id)
                if not can_process:
                    logger.warning(f"Organization {org_id} exceeded limits")
                    return ProcessingResult(
                        email_id=email_message.id,
                        should_forward=False,
                        block_reason="Organization email limit exceeded"
                    )
            
            # Step 3: Process email content through ContentProcessor
            context = ProcessingContext(
                organization_id=org_id,
                user_id=user_id,
                source_plugin=email_message.source_plugin or "unknown"
            )
            
            processing_result = self.content_processor.process_email_content(email_message, context)
            
            # Step 4: Extract forwarding decision from processing result
            should_forward = processing_result.should_forward
            
            # Step 5: Log the email processing
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_email(
                email_message=email_message,
                result=ProcessingResult(
                    email_id=email_message.id,
                    should_forward=should_forward,
                    block_reason=processing_result.block_reason,
                    toxicity_score=processing_result.toxicity_score,
                    horsemen_detected=processing_result.analysis.horsemen_detected,
                    ai_analysis=self._convert_analysis_to_dict(processing_result.analysis),
                    processing_time_ms=processing_time
                )
            )
            
            # Step 6: Forward email if approved
            if should_forward:
                await self._forward_email(email_message)
            
            return ProcessingResult(
                email_id=email_message.id,
                should_forward=should_forward,
                block_reason=processing_result.block_reason,
                toxicity_score=processing_result.toxicity_score,
                horsemen_detected=processing_result.analysis.horsemen_detected,
                ai_analysis=self._convert_analysis_to_dict(processing_result.analysis),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing email {email_message.id}: {e}", exc_info=True)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return ProcessingResult(
                email_id=email_message.id,
                should_forward=False,
                block_reason=f"Processing error: {str(e)}",
                processing_time_ms=processing_time
            )
    
    async def _identify_context(self, email_message: EmailMessage) -> tuple[Optional[UUID], Optional[UUID]]:
        """Identify organization and user from email addresses."""
        # For now, return None - will be implemented with database lookups
        # This would look up based on to_addresses domain matching organization
        return None, None
    
    async def _check_organization_limits(self, org_id: UUID) -> bool:
        """Check if organization can process more emails."""
        try:
            # Query organization from database
            org = await Organization.objects().where(
                Organization.id == org_id
            ).first()
            
            if not org:
                return False
                
            # Check if active
            if not org.is_active:
                return False
                
            # Check monthly limit
            if org.emails_processed_month >= org.monthly_email_limit:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking organization limits: {e}")
            return False
    
    def _convert_analysis_to_dict(self, analysis) -> Dict[str, Any]:
        """Convert AnalysisResult dataclass to dict for logging compatibility."""
        return {
            'classification': analysis.classification,
            'horsemen_detected': analysis.horsemen_detected,
            'reasoning': analysis.reasoning,
            'specific_examples': analysis.specific_examples,
            'confidence_score': analysis.confidence_score
        }
    
    async def _log_email(self, email_message: EmailMessage, result: ProcessingResult):
        """Log email processing to database."""
        try:
            # Create email log entry (handle nullable organization)
            email_log = EmailLog(
                organization=email_message.organization_id,
                user=email_message.user_id,
                from_address=email_message.from_address,
                to_addresses=email_message.to_addresses,
                subject=email_message.subject,
                message_id=email_message.message_id,
                status="forwarded" if result.should_forward else "blocked",
                ai_analysis=result.ai_analysis,
                toxicity_score=result.toxicity_score,
                horsemen_detected=result.horsemen_detected,
                blocked_content=not result.should_forward,
                original_content=email_message.text_content[:5000],  # Truncate for storage
                processing_time_ms=result.processing_time_ms,
                plugin_used=email_message.source_plugin,
                received_at=email_message.received_at
            )
            await email_log.save()
            logger.info(f"Logged email {email_message.id} to database")
            
        except Exception as e:
            logger.error(f"Failed to log email: {e}", exc_info=True)
    
    async def _forward_email(self, email_message: EmailMessage):
        """Forward approved email to recipients."""
        if not self.email_sender:
            logger.warning(f"No email sender configured, cannot forward email {email_message.id}")
            return
        
        # Prepare AI result - since email reached here, it passed filtering (SAFE)
        ai_result = {'ai_classification': 'SAFE'}
        
        # Prepare original email data
        original_email_data = {
            'original_subject': email_message.subject or 'No Subject',
            'original_sender': email_message.from_address,
            'original_body': email_message.text_content or email_message.html_content or 'No content',
            'message_id': email_message.message_id,
            'content': email_message.text_content or email_message.html_content or 'No content'
        }
        
        # Send to each recipient
        successful_sends = 0
        for to_address in email_message.to_addresses:
            try:
                success = await self.email_sender.send_filtered_email(
                    recipient_shield_address=to_address,
                    ai_result=ai_result,
                    original_email_data=original_email_data
                )
                
                if success:
                    successful_sends += 1
                    logger.info(f"Successfully forwarded email {email_message.id} to {to_address}")
                else:
                    logger.error(f"Failed to forward email {email_message.id} to {to_address}")
                    
            except Exception as e:
                logger.error(f"Error forwarding email {email_message.id} to {to_address}: {e}", exc_info=True)
        
        logger.info(f"Forwarded email {email_message.id} to {successful_sends}/{len(email_message.to_addresses)} recipients")