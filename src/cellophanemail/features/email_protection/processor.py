"""Email protection processor - orchestrates the protection flow."""

import logging
from typing import Optional, List
from datetime import datetime

from ...providers.contracts import EmailMessage
from .analyzer import FourHorsemenAnalyzer
from .enhanced_analyzer import EnhancedFourHorsemenAnalyzer
from .models import ProtectionResult, ThreatLevel
from .storage import ProtectionLogStorage
from .shared_context import SharedContext
from .llm_analyzer import SimpleLLMAnalyzer
from .graduated_decision_maker import GraduatedDecisionMaker, ProtectionAction

logger = logging.getLogger(__name__)


class EmailProtectionProcessor:
    """
    Processes emails through protection pipeline with shared context.
    Now includes iterative analysis through 4 phases.
    """
    
    def __init__(self, llm_analyzer: Optional[SimpleLLMAnalyzer] = None):
        self.analyzer = EnhancedFourHorsemenAnalyzer()
        self.storage = ProtectionLogStorage()
        self.shared_context = SharedContext(llm_analyzer)
        self.graduated_decision_maker = GraduatedDecisionMaker()
        
    async def process_email(
        self, 
        email: EmailMessage,
        user_email: str,
        organization_id: Optional[str] = None
    ) -> ProtectionResult:
        """
        Process an email through enhanced protection pipeline with shared context.
        
        New flow:
        1. Start new email in shared context
        2. Phase 1: Extract facts and analyze manner
        3. Phase 2: Summarize fact presentation patterns
        4. Phase 3: Analyze non-factual content
        5. Phase 4: Extract implicit messages
        6. Enhanced Four Horsemen analysis
        7. Make protection decision
        
        Args:
            email: The email message to process
            user_email: The real email address to forward to
            organization_id: Optional organization ID for quota checking
            
        Returns:
            ProtectionResult with enhanced analysis and reasoning
        """
        logger.info(f"Processing email {email.message_id} for protection with shared context")
        
        # Prepare content for analysis
        content = self._prepare_content(email)
        
        # Start new email analysis in shared context
        self.shared_context.start_new_email(content, email.from_address)
        
        # Phase 1: Extract facts and analyze their manner
        phase1_result = self.shared_context.update_phase1_facts()
        logger.debug(f"Phase 1 complete: {phase1_result.data['total_facts']} facts, "
                    f"ratio: {phase1_result.data['fact_ratio']:.2f}")
        
        # Phase 2: Summarize manner patterns
        phase2_result = self.shared_context.update_phase2_manner_summary()
        if phase2_result:
            logger.debug(f"Phase 2 complete: {phase2_result.data['overall_manner']}")
        
        # Phase 3: Analyze non-factual content
        phase3_result = self.shared_context.update_phase3_non_factual()
        logger.debug(f"Phase 3 complete: {len(phase3_result.data.get('personal_attacks', []))} attacks detected")
        
        # Phase 4: Extract implicit messages
        phase4_result = self.shared_context.update_phase4_implicit()
        logger.debug(f"Phase 4 complete: {len(phase4_result.data['implicit_threats'])} implicit threats")
        
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
        
        # Enhanced Four Horsemen analysis with shared context
        analysis = self._enhanced_four_horsemen_analysis(content, email.from_address)
        
        # Enhanced protection decision using graduated decision maker
        original_content = self._prepare_content(email)
        protection_decision = self.graduated_decision_maker.make_decision(analysis, original_content)
        
        # Map graduated decision to binary decision for backward compatibility
        should_forward = protection_decision.action != ProtectionAction.BLOCK_ENTIRELY
        enhanced_block_reason = None if should_forward else protection_decision.reasoning
        
        # Create enhanced result
        result = ProtectionResult(
            should_forward=should_forward,
            analysis=analysis,
            block_reason=enhanced_block_reason,
            forwarded_to=[user_email] if should_forward else None,
            logged_at=datetime.now(),
            message_id=email.message_id,
            # Graduated decision fields
            protection_action=protection_decision.action,
            processed_content=protection_decision.processed_content,
            decision_reasoning=protection_decision.reasoning
        )
        
        # Enhanced logging with shared context
        await self.storage.log_protection_decision(email, result)
        
        logger.info(f"Email {email.message_id} enhanced protection decision: "
                   f"forward={should_forward}, context_iteration={self.shared_context.iteration}")
        
        return result
    
    def _prepare_content(self, email: EmailMessage) -> str:
        """Prepare email content for analysis."""
        parts = []
        
        # Include subject
        if email.subject:
            parts.append(f"Subject: {email.subject}")
        
        # Include text body
        # Support both naming conventions during migration
        text_body = getattr(email, 'text_body', None) or getattr(email, 'text_content', None)
        html_body = getattr(email, 'html_body', None) or getattr(email, 'html_content', None)
        
        if text_body:
            parts.append(text_body)
        
        # If no text body, try to extract from HTML (simplified)
        elif html_body:
            # In production, use proper HTML parsing
            import re
            text = re.sub('<[^<]+?>', '', html_body)
            parts.append(text)
        
        return "\n".join(parts)
    
    def _enhanced_four_horsemen_analysis(self, content: str, sender: str):
        """
        Enhanced Four Horsemen analysis incorporating shared context insights.
        Uses EnhancedFourHorsemenAnalyzer with configurable weights and sophisticated detection.
        """
        # Use enhanced analyzer with shared context - all sophistication is handled internally
        return self.analyzer.analyze_with_context(content, sender, self.shared_context)
    
    def _make_enhanced_protection_decision(self, analysis) -> tuple[bool, Optional[str]]:
        """
        Make protection decision with enhanced reasoning from shared context.
        
        Returns:
            tuple: (should_forward, detailed_block_reason)
        """
        # Base decision
        should_forward = analysis.safe and analysis.threat_level in [ThreatLevel.SAFE, ThreatLevel.LOW]
        
        if should_forward:
            return True, None
        
        # Enhanced block reasoning with context
        context_summary = self.shared_context.get_current_analysis_summary()
        phases = context_summary.get("phases", {})
        
        # Build detailed block reason
        reasons = []
        
        # Fact-based reasoning
        fact_ratio = context_summary.get("fact_ratio", 0.0)
        if fact_ratio < 0.2:
            reasons.append(f"Email is {(1-fact_ratio)*100:.1f}% non-factual content")
        
        # Manner-based reasoning
        manner_data = phases.get("manner_summary", {})
        overall_manner = manner_data.get("overall_manner", "unknown")
        if overall_manner == "predominantly_negative":
            negative_ratio = manner_data.get("negative_ratio", 0.0)
            reasons.append(f"Facts presented in negative manner ({negative_ratio:.1%} of facts)")
        
        # Personal attack reasoning
        non_factual_data = phases.get("non_factual_analysis", {})
        personal_attacks = non_factual_data.get("personal_attacks", [])
        if personal_attacks:
            reasons.append(f"Contains personal attacks: {', '.join(personal_attacks)}")
        
        # Implicit threat reasoning
        implicit_data = phases.get("implicit_analysis", {})
        implicit_threats = implicit_data.get("implicit_threats", [])
        if implicit_threats:
            reasons.append(f"Implicit threats detected: {', '.join(implicit_threats)}")
        
        # Four Horsemen reasoning
        if analysis.horsemen_detected:
            horsemen = [h.horseman for h in analysis.horsemen_detected]
            reasons.append(f"Four Horsemen patterns: {', '.join(horsemen)}")
        
        # Historical context reasoning
        historical = context_summary.get("historical_context", {})
        if historical.get("escalation_detected"):
            reasons.append(f"Escalation pattern detected over {historical.get('previous_iterations', 0)} emails")
        
        # Combine all reasons
        detailed_reason = " | ".join(reasons) if reasons else f"Threat level: {analysis.threat_level.value}"
        
        return False, detailed_reason
    
    async def _check_org_limits(self, organization_id: str) -> bool:
        """
        Check if organization is within email limits.
        Simplified for demo - in production would check database.
        """
        # TODO: Implement actual organization limit checking
        return True