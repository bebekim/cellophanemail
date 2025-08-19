"""Email protection processor - orchestrates the protection flow."""

import logging
from typing import Optional, List
from datetime import datetime

from ...providers.contracts import EmailMessage
from .analyzer import FourHorsemenAnalyzer
from .models import ProtectionResult, ThreatLevel
from .storage import ProtectionLogStorage

logger = logging.getLogger(__name__)


class EmailProtectionProcessor:
    """
    Processes emails through protection pipeline.
    Self-contained - doesn't depend on external services.
    """
    
    def __init__(self):
        self.analyzer = FourHorsemenAnalyzer()
        self.storage = ProtectionLogStorage()
        
    async def process_email(
        self, 
        email: EmailMessage,
        user_email: str,
        organization_id: Optional[str] = None
    ) -> ProtectionResult:
        """
        Process an email through the protection pipeline.
        
        Args:
            email: The email message to process
            user_email: The real email address to forward to
            organization_id: Optional organization ID for quota checking
            
        Returns:
            ProtectionResult with decision and analysis
        """
        logger.info(f"Processing email {email.message_id} for protection")
        
        # Prepare content for analysis
        content = self._prepare_content(email)
        
        # Analyze content
        analysis = self.analyzer.analyze(content, email.from_address)
        
        # Check organization limits if applicable
        if organization_id:
            within_limits = await self._check_org_limits(organization_id)
            if not within_limits:
                logger.warning(f"Organization {organization_id} exceeded email limits")
                return ProtectionResult(
                    should_forward=False,
                    analysis=None,
                    block_reason="Organization email limit exceeded",
                    forwarded_to=None,
                    logged_at=datetime.now(),
                    message_id=email.message_id
                )
        
        # Make forwarding decision
        should_forward = analysis.safe and analysis.threat_level in [ThreatLevel.SAFE, ThreatLevel.LOW]
        
        # Determine block reason if not forwarding
        block_reason = None
        if not should_forward:
            if analysis.horsemen_detected:
                horsemen = ", ".join([h.horseman for h in analysis.horsemen_detected])
                block_reason = f"Detected harmful content: {horsemen}"
            else:
                block_reason = f"Threat level too high: {analysis.threat_level.value}"
        
        # Create result
        result = ProtectionResult(
            should_forward=should_forward,
            analysis=analysis,
            block_reason=block_reason,
            forwarded_to=[user_email] if should_forward else None,
            logged_at=datetime.now(),
            message_id=email.message_id
        )
        
        # Log the decision
        await self.storage.log_protection_decision(email, result)
        
        logger.info(f"Email {email.message_id} protection decision: "
                   f"forward={should_forward}, threat_level={analysis.threat_level.value}")
        
        return result
    
    def _prepare_content(self, email: EmailMessage) -> str:
        """Prepare email content for analysis."""
        parts = []
        
        # Include subject
        if email.subject:
            parts.append(f"Subject: {email.subject}")
        
        # Include text body
        if email.text_body:
            parts.append(email.text_body)
        
        # If no text body, try to extract from HTML (simplified)
        elif email.html_body:
            # In production, use proper HTML parsing
            import re
            text = re.sub('<[^<]+?>', '', email.html_body)
            parts.append(text)
        
        return "\n".join(parts)
    
    async def _check_org_limits(self, organization_id: str) -> bool:
        """
        Check if organization is within email limits.
        Simplified for demo - in production would check database.
        """
        # TODO: Implement actual organization limit checking
        return True