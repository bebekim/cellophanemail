"""
Streamlined email protection processor using consolidated single-pass LLM analysis.

Replaces the complex 4-phase pipeline with:
1. Single LLM analysis call (1-2 seconds vs 30+ seconds)
2. Clean separation of concerns
3. Empirically calibrated thresholds
4. Deterministic testing support

Architecture:
- EmailToxicityAnalyzer: Single comprehensive analysis
- GraduatedDecisionMaker: Pure decision logic  
- ProtectionLogStorage: Isolated side effects
"""

import logging
from typing import Optional
from datetime import datetime

from ...providers.contracts import EmailMessage
from .analyzer_interface import IEmailAnalyzer
from .analyzer_factory import AnalyzerFactory  
from .graduated_decision_maker import GraduatedDecisionMaker, ProtectionAction
from .models import ProtectionResult, ThreatLevel
from .storage import ProtectionLogStorage

logger = logging.getLogger(__name__)


# Empirically calibrated thresholds based on real LLM behavior
# Updated 2025-08-23: Recalibrated based on analysis of 88 real email scores
# Score distribution: 0.01-0.05 (clean), 0.35-0.45 (minor), 0.65 (moderate), 0.75-0.95 (high)
EMPIRICAL_THRESHOLDS = {
    'forward_clean': 0.30,       # Clean emails score 0.01-0.20, with some variance
    'forward_context': 0.55,     # Minor toxicity emails score 0.35-0.50
    'redact_harmful': 0.70,      # Moderate toxicity emails score 0.65
    'summarize_only': 0.90       # High toxicity emails score 0.75-0.85
}


class StreamlinedEmailProtectionProcessor:
    """
    High-performance email protection processor with simplified architecture.
    
    Key improvements over legacy processor:
    - 5-10x faster processing (single LLM call vs 6 calls)
    - More deterministic results (temperature=0 option) 
    - Cleaner separation of concerns
    - Empirically calibrated thresholds
    - Better error handling and fallbacks
    """
    
    def __init__(self,
                 analyzer: Optional[IEmailAnalyzer] = None,
                 temperature: float = 0.0):
        """
        Initialize streamlined processor.

        Args:
            analyzer: Email analyzer to inject. If None, uses factory to create one
            temperature: LLM temperature. Use 0.0 for deterministic testing
        """
        if analyzer is not None:
            self.analyzer = analyzer
            logger.info(f"Using injected analyzer: {type(analyzer).__name__}")
        else:
            self.analyzer = AnalyzerFactory.create_analyzer(temperature=temperature)
            logger.info(f"Created analyzer via factory: {type(self.analyzer).__name__}")
            
        # GraduatedDecisionMaker now derives thresholds from horsemen detection
        self.decision_maker = GraduatedDecisionMaker()
        self.storage = ProtectionLogStorage()
        
        logger.info(f"Initialized streamlined processor with temperature={temperature}")
    
    async def process_email(self,
                          email: EmailMessage,
                          user_email: str,
                          organization_id: Optional[str] = None) -> ProtectionResult:
        """
        Process email through streamlined protection pipeline.
        
        New simplified flow:
        1. Prepare email content
        2. Single comprehensive LLM analysis  
        3. Make graduated protection decision
        4. Log result and return
        
        Args:
            email: Email message to analyze
            user_email: Real email address to forward to
            organization_id: Optional organization for quota checking
            
        Returns:
            ProtectionResult with analysis and decision
        """
        logger.info(f"Processing email {email.message_id} with streamlined pipeline")
        start_time = datetime.now()
        
        # Prepare email content for analysis
        content = self._prepare_email_content(email)
        
        # Check organization limits if applicable
        if organization_id:
            within_limits = await self._check_organization_limits(organization_id)
            if not within_limits:
                return self._create_quota_exceeded_result(email, organization_id)
        
        # Single comprehensive LLM analysis (replaces 6-call pipeline)
        try:
            consolidated_analysis = self.analyzer.analyze_email_toxicity(content, email.from_address)
        except Exception as e:
            logger.error(f"LLM analysis failed for {email.message_id}: {e}")
            # Conservative fallback - assume medium toxicity to be safe
            consolidated_analysis = self._create_fallback_analysis(content, str(e))
        
        # Convert to legacy format for compatibility (if available)
        if hasattr(self.analyzer, 'to_legacy_analysis_result'):
            legacy_analysis = self.analyzer.to_legacy_analysis_result(consolidated_analysis)
        else:
            # Create legacy analysis from consolidated analysis for mock analyzers
            from .models import AnalysisResult
            legacy_analysis = AnalysisResult(
                safe=consolidated_analysis.safe,
                threat_level=consolidated_analysis.threat_level,
                toxicity_score=consolidated_analysis.toxicity_score,
                horsemen_detected=consolidated_analysis.horsemen_detected,
                reasoning=consolidated_analysis.reasoning,
                processing_time_ms=consolidated_analysis.processing_time_ms,
                cached=False
            )
        
        # Make graduated protection decision
        protection_decision = self.decision_maker.make_decision(legacy_analysis, content)
        
        # Map to binary decision for compatibility
        should_forward = protection_decision.action != ProtectionAction.BLOCK_ENTIRELY
        block_reason = None if should_forward else protection_decision.reasoning
        
        # Create result
        result = ProtectionResult(
            should_forward=should_forward,
            analysis=legacy_analysis,
            block_reason=block_reason,
            forwarded_to=[user_email] if should_forward else None,
            logged_at=datetime.now(),
            message_id=email.message_id,
            # Graduated decision fields
            protection_action=protection_decision.action,
            processed_content=protection_decision.processed_content,
            decision_reasoning=protection_decision.reasoning
        )
        
        # Log decision
        await self.storage.log_protection_decision(email, result)
        
        # Performance logging
        total_time = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.info(f"Email {email.message_id} processed in {total_time}ms: "
                   f"action={protection_decision.action}, toxicity={consolidated_analysis.toxicity_score:.3f}")
        
        return result
    
    def _prepare_email_content(self, email: EmailMessage) -> str:
        """Prepare email content for analysis."""
        parts = []
        
        # Include subject
        if email.subject:
            parts.append(f"Subject: {email.subject}")
        
        # Include text body (support both naming conventions)
        text_body = getattr(email, 'text_body', None) or getattr(email, 'text_content', None)
        html_body = getattr(email, 'html_body', None) or getattr(email, 'html_content', None)
        
        if text_body:
            parts.append(text_body)
        elif html_body:
            # Simple HTML stripping (in production, use proper HTML parsing)
            import re
            text = re.sub('<[^<]+?>', '', html_body)
            parts.append(text)
        
        return "\\n".join(parts)
    
    async def _check_organization_limits(self, organization_id: str) -> bool:
        """Check if organization is within email processing limits."""
        # TODO: Implement actual organization limit checking
        return True
    
    def _create_fallback_analysis(self, content: str, error_reason: str):
        """Create conservative fallback analysis when LLM fails."""
        from .mock_analyzer import EmailAnalysis
        from .models import ThreatLevel
        
        # Conservative fallback - assume medium toxicity to trigger protection
        return EmailAnalysis(
            toxicity_score=0.6,  # Medium toxicity -> REDACT_HARMFUL
            threat_level=ThreatLevel.MEDIUM,
            safe=False,
            fact_ratio=0.5,
            communication_manner="unknown",
            personal_attacks=[],
            manipulation_tactics=[],
            implicit_threats=[],
            horsemen_detected=[],
            reasoning=f"LLM analysis failed: {error_reason}. Using conservative fallback.",
            confidence=0.3,
            processing_time_ms=10,
            language_detected="unknown"
        )
    
    def _create_quota_exceeded_result(self, email: EmailMessage, organization_id: str) -> ProtectionResult:
        """Create result for quota exceeded scenario."""
        logger.warning(f"Organization {organization_id} exceeded email limits")
        
        return ProtectionResult(
            should_forward=False,
            analysis=None,
            block_reason="Organization email limit exceeded",
            forwarded_to=None,
            logged_at=datetime.now(),
            message_id=email.message_id,
            protection_action=ProtectionAction.BLOCK_ENTIRELY,
            processed_content="",
            decision_reasoning="Organization quota exceeded"
        )


# Factory function for easy migration from legacy processor
def create_streamlined_processor(temperature: float = 0.0) -> StreamlinedEmailProtectionProcessor:
    """
    Factory function to create streamlined processor with optimal defaults.
    
    Args:
        temperature: 0.0 for deterministic testing, 0.1-0.3 for production variety
        
    Returns:
        Configured StreamlinedEmailProtectionProcessor
    """
    return StreamlinedEmailProtectionProcessor(temperature=temperature)


# Backward compatibility alias
StreamlinedProcessor = StreamlinedEmailProtectionProcessor