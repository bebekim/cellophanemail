"""Email processing pipeline with Four Horsemen analysis."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from .email_message import EmailMessage
from .content_analyzer import ContentAnalyzer
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
    
    def __init__(self):
        """Initialize the email processor."""
        self.analyzer = ContentAnalyzer()
        
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
            
            # Step 3: Perform Four Horsemen analysis
            analysis_result = self.analyzer.analyze_content(
                content=email_message.text_content or email_message.html_content,
                sender=email_message.from_address
            )
            
            # Step 4: Determine if email should be forwarded
            should_forward = self._should_forward_email(analysis_result)
            
            # Step 5: Log the email processing
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_email(
                email_message=email_message,
                result=ProcessingResult(
                    email_id=email_message.id,
                    should_forward=should_forward,
                    block_reason=None if should_forward else "Four Horsemen detected",
                    toxicity_score=self._calculate_toxicity_score(analysis_result),
                    horsemen_detected=analysis_result.get("horsemen_detected", []),
                    ai_analysis=analysis_result,
                    processing_time_ms=processing_time
                )
            )
            
            # Step 6: Forward email if approved
            if should_forward:
                await self._forward_email(email_message)
            
            return ProcessingResult(
                email_id=email_message.id,
                should_forward=should_forward,
                block_reason=None if should_forward else "Content filtered by Four Horsemen analysis",
                toxicity_score=self._calculate_toxicity_score(analysis_result),
                horsemen_detected=analysis_result.get("horsemen_detected", []),
                ai_analysis=analysis_result,
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
    
    def _calculate_toxicity_score(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate toxicity score from analysis result."""
        classification = analysis_result.get("classification", "SAFE")
        horsemen_count = len(analysis_result.get("horsemen_detected", []))
        
        # Convert classification to numeric score
        score_map = {
            "SAFE": 0.0,
            "WARNING": 0.3,
            "HARMFUL": 0.7,
            "ABUSIVE": 1.0
        }
        
        base_score = score_map.get(classification, 0.0)
        
        # Adjust based on horsemen count
        if horsemen_count > 0:
            base_score = max(base_score, 0.5 + (horsemen_count * 0.1))
            
        return min(base_score, 1.0)

    def _should_forward_email(self, analysis_result: Dict[str, Any]) -> bool:
        """Determine if email should be forwarded based on analysis."""
        # Check toxicity threshold
        toxicity_score = self._calculate_toxicity_score(analysis_result)
        if toxicity_score > 0.7:  # Configurable threshold
            return False
            
        # Check for Four Horsemen
        horsemen = analysis_result.get("horsemen_detected", [])
        if len(horsemen) > 0:
            # Could have more nuanced logic here
            # For now, block if any horseman detected
            return False
            
        return True
    
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
        # This will be implemented with actual email sending logic
        # For now, just log
        logger.info(f"Would forward email {email_message.id} to {email_message.to_addresses}")
        # TODO: Implement actual forwarding via SMTP or API