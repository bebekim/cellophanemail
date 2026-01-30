"""InMemoryProcessor for processing emails without database storage."""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from analysis_engine import decide_action, ThreatLevel

from .ephemeral_email import EphemeralEmail
from .graduated_decision_maker import ProtectionAction
from .analyzer_interface import IEmailAnalyzer
from .analyzer_factory import AnalyzerFactory
from .contracts import EmailProcessorInterface

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """
    Result of in-memory email processing.

    Simplified result format focused on delivery decisions.
    """
    action: ProtectionAction
    threat_level: ThreatLevel
    requires_delivery: bool
    delivery_targets: List[str]
    processed_content: str
    processing_time_ms: int
    reasoning: Optional[str] = None


class InMemoryProcessor(EmailProcessorInterface):
    """
    In-memory email processor for privacy-focused email protection.

    Provides lightweight email toxicity analysis and protection decisions without
    persisting any email content to databases. Designed for maximum privacy and
    immediate processing with quick delivery decisions.

    Uses Four Horsemen detection with contempt-weighted model (Gottman research).
    """

    def __init__(self, temperature: float = 0.0, use_llm: bool = True, analyzer: Optional[IEmailAnalyzer] = None):
        """
        Initialize InMemoryProcessor with specified analysis parameters.

        Args:
            temperature: Analysis temperature (0.0 for deterministic results)
            use_llm: Whether to use LLM analyzer (True) or simple heuristics (False)
            analyzer: Optional analyzer to inject (for testing). If None, uses factory.
        """
        self.temperature = temperature
        self.use_llm = use_llm

        # Use injected analyzer or create via factory
        if analyzer is not None:
            self.llm_analyzer = analyzer
            logger.info(f"Using injected analyzer: {type(analyzer).__name__}")
        elif self.use_llm:
            try:
                self.llm_analyzer = AnalyzerFactory.create_analyzer(temperature=temperature)
                logger.info(f"Created analyzer via factory: {type(self.llm_analyzer).__name__}")
            except (ValueError, Exception) as e:
                logger.error(f"Failed to create analyzer: {e}. No fallback available.")
                raise RuntimeError(f"LLM analyzer creation failed: {e}")
        else:
            self.llm_analyzer = None

    async def process_email(self, email: EphemeralEmail) -> ProcessingResult:
        """
        Process an ephemeral email without database storage.

        Args:
            email: EphemeralEmail instance to process

        Returns:
            ProcessingResult with action and delivery information
        """
        logger.info(f"Processing ephemeral email {email.message_id}")

        # Analyze content for toxicity (using LLM or heuristics)
        content = email.get_content_for_analysis()

        if self.use_llm and self.llm_analyzer:
            # Use LLM for analysis - no fallback to heuristics
            try:
                analysis = self.llm_analyzer.analyze_email_toxicity(content, email.from_address)
                threat_level = analysis.threat_level
                horsemen_detected = analysis.horsemen_detected
            except Exception as e:
                logger.error(f"LLM analysis failed: {e}")
                raise RuntimeError(f"Email analysis failed, no fallback available: {e}")
        else:
            # Only use heuristics if LLM is explicitly disabled
            threat_level, horsemen_detected = self._analyze_content_heuristics(content)

        # Use analysis_engine's decide_action for consistent logic
        action = decide_action(horsemen_detected)

        # Apply content processing based on action
        if action == ProtectionAction.FORWARD_CLEAN:
            requires_delivery = True
            processed_content = content
            reasoning = f"Clean content (threat_level: {threat_level.value})"

        elif action == ProtectionAction.FORWARD_WITH_CONTEXT:
            requires_delivery = True
            processed_content = self._add_context_warning(content)
            reasoning = f"Minor toxicity (threat_level: {threat_level.value}) - adding context warning"

        elif action == ProtectionAction.REDACT_HARMFUL:
            requires_delivery = True
            processed_content = self._redact_toxic_content(content)
            reasoning = f"Moderate toxicity (threat_level: {threat_level.value}) - redacting harmful content"

        elif action == ProtectionAction.SUMMARIZE_ONLY:
            requires_delivery = True
            processed_content = self._create_safe_summary(content)
            reasoning = f"High toxicity (threat_level: {threat_level.value}) - providing factual summary only"

        else:  # BLOCK_ENTIRELY
            requires_delivery = False
            processed_content = ""
            reasoning = f"Extreme toxicity (threat_level: {threat_level.value}) - blocking entirely"

        delivery_targets = [email.user_email] if requires_delivery else []

        return ProcessingResult(
            action=action,
            threat_level=threat_level,
            requires_delivery=requires_delivery,
            delivery_targets=delivery_targets,
            processed_content=processed_content,
            processing_time_ms=150,  # Simulated processing time
            reasoning=reasoning
        )

    def _analyze_content_heuristics(self, content: str) -> tuple:
        """
        Simple heuristic analysis returning threat level and empty horsemen list.

        This is a fallback when LLM is disabled.
        Returns (ThreatLevel, []) tuple.
        """
        from .models import HorsemanDetection

        # Define toxic keywords by severity level
        contempt_words = ['worthless', 'pathetic', 'disgusting', 'loser', 'idiot']
        criticism_words = ['terrible', 'awful', 'stupid', 'incompetent']
        mild_words = ['annoying', 'frustrating', 'disappointing']

        content_lower = content.lower()

        horsemen = []

        # Check for contempt
        contempt_matches = [w for w in contempt_words if w in content_lower]
        if contempt_matches:
            horsemen.append(HorsemanDetection(
                horseman="contempt",
                confidence=0.8,
                indicators=contempt_matches[:3],
                severity="high"
            ))

        # Check for criticism
        criticism_matches = [w for w in criticism_words if w in content_lower]
        if criticism_matches:
            horsemen.append(HorsemanDetection(
                horseman="criticism",
                confidence=0.7,
                indicators=criticism_matches[:3],
                severity="medium"
            ))

        # Check for mild toxic language
        if any(w in content_lower for w in mild_words) and not horsemen:
            horsemen.append(HorsemanDetection(
                horseman="criticism",
                confidence=0.5,
                indicators=mild_words[:2],
                severity="low"
            ))

        threat_level = ThreatLevel.from_horsemen(horsemen)
        return (threat_level, horsemen)

    def _add_context_warning(self, content: str) -> str:
        """Add context warning to content with minor toxicity."""
        warning = "[CONTEXT: This email contains language that may be considered mildly inappropriate]"
        return f"{content}\n\n{warning}"

    def _redact_toxic_content(self, content: str) -> str:
        """Redact toxic words from content."""
        toxic_words = ['hate', 'stupid', 'idiot', 'disgusting', 'pathetic', 'terrible', 'awful']

        processed = content
        redactions = 0

        for word in toxic_words:
            if word in processed.lower():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                processed = pattern.sub('[REDACTED]', processed)
                redactions += 1

        if redactions > 0:
            processed += f"\n\n[NOTE: {redactions} inappropriate terms were redacted for your protection]"

        return processed

    def _create_safe_summary(self, content: str) -> str:
        """Create a factual summary removing emotional/toxic content."""
        # Extract factual information (simplified implementation)
        lines = content.split('\n')
        safe_lines = []

        for line in lines:
            # Keep lines that seem factual (contain numbers, dates, etc.)
            if any(char.isdigit() for char in line) or 'meeting' in line.lower() or 'project' in line.lower():
                safe_lines.append(line)

        if safe_lines:
            summary = "[FACTUAL SUMMARY]\n" + "\n".join(safe_lines)
        else:
            summary = "[FACTUAL SUMMARY]\nNo clear factual information could be safely extracted from this message."

        return summary
