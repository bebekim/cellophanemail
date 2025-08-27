"""InMemoryProcessor for processing emails without database storage."""

import logging
from dataclasses import dataclass
from typing import List, Optional

from .ephemeral_email import EphemeralEmail
from .graduated_decision_maker import ProtectionAction
from .llama_analyzer import LlamaAnalyzer
from .contracts import EmailProcessorInterface

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """
    Result of in-memory email processing.
    
    Simplified result format focused on delivery decisions.
    """
    action: ProtectionAction
    toxicity_score: float
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
    
    Features:
    - Zero-persistence processing (content never stored)
    - Simple but effective toxicity detection
    - Graduated protection actions based on threat levels
    - Deterministic results for testing (temperature=0.0)
    - Extensible architecture for future LLM integration
    
    Architecture Notes:
    This is the minimal viable implementation using simple heuristics.
    Future versions will integrate with the StreamlinedEmailProtectionProcessor
    once database storage dependencies are removed from that component.
    """
    
    def __init__(self, temperature: float = 0.0, use_llm: bool = True):
        """
        Initialize InMemoryProcessor with specified analysis parameters.
        
        Args:
            temperature: Analysis temperature (0.0 for deterministic results, 
                        higher values for more varied analysis in production)
            use_llm: Whether to use LlamaAnalyzer (True) or simple heuristics (False)
        """
        self.temperature = temperature
        self.use_llm = use_llm
        
        # Initialize LLM analyzer if requested
        if self.use_llm:
            try:
                self.llm_analyzer = LlamaAnalyzer(temperature=temperature)
            except (ValueError, Exception) as e:
                logger.warning(f"Failed to initialize LlamaAnalyzer: {e}. Falling back to heuristics.")
                self.use_llm = False
                self.llm_analyzer = None
        else:
            self.llm_analyzer = None
        
        # Toxicity analysis thresholds aligned with graduated decision maker
        self.thresholds = {
            'forward_clean': 0.30,      # Very clean content
            'forward_context': 0.55,    # Minor issues, add context
            'redact_harmful': 0.70,     # Moderate issues, redact parts
            'summarize_only': 0.90      # High toxicity, summarize only
        }
        
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
            # Use LLM for analysis
            llm_result = self.llm_analyzer.analyze_toxicity(content)
            toxicity_score = llm_result.get('toxicity_score', 0.0)
        else:
            # Fall back to heuristics
            toxicity_score = self._analyze_content_toxicity(content)
        
        # Graduated decision making using configured thresholds
        if toxicity_score < self.thresholds['forward_clean']:
            action = ProtectionAction.FORWARD_CLEAN
            requires_delivery = True
            processed_content = content
            reasoning = f"Clean content (toxicity: {toxicity_score:.3f})"
            
        elif toxicity_score < self.thresholds['forward_context']:
            action = ProtectionAction.FORWARD_WITH_CONTEXT
            requires_delivery = True
            processed_content = self._add_context_warning(content)
            reasoning = f"Minor toxicity (toxicity: {toxicity_score:.3f}) - adding context warning"
            
        elif toxicity_score < self.thresholds['redact_harmful']:
            action = ProtectionAction.REDACT_HARMFUL
            requires_delivery = True
            processed_content = self._redact_toxic_content(content)
            reasoning = f"Moderate toxicity (toxicity: {toxicity_score:.3f}) - redacting harmful content"
            
        elif toxicity_score < self.thresholds['summarize_only']:
            action = ProtectionAction.SUMMARIZE_ONLY
            requires_delivery = True
            processed_content = self._create_safe_summary(content)
            reasoning = f"High toxicity (toxicity: {toxicity_score:.3f}) - providing factual summary only"
            
        else:
            action = ProtectionAction.BLOCK_ENTIRELY
            requires_delivery = False
            processed_content = ""
            reasoning = f"Extreme toxicity (toxicity: {toxicity_score:.3f}) - blocking entirely"
        
        delivery_targets = [email.user_email] if requires_delivery else []
        
        return ProcessingResult(
            action=action,
            toxicity_score=toxicity_score,
            requires_delivery=requires_delivery,
            delivery_targets=delivery_targets,
            processed_content=processed_content,
            processing_time_ms=150,  # Simulated processing time
            reasoning=reasoning
        )
    
    def _analyze_content_toxicity(self, content: str) -> float:
        """
        Simple toxicity analysis using keyword-based heuristics.
        
        In production, this would call the actual LLM analyzer.
        Returns a score from 0.0 (clean) to 1.0 (extremely toxic).
        """
        # Define toxic keywords by severity level
        mild_toxic = ['terrible', 'awful', 'annoying', 'frustrating']
        moderate_toxic = ['hate', 'stupid', 'idiot', 'disgusting', 'pathetic']
        severe_toxic = ['worthless', 'despise', 'loathe']
        
        content_lower = content.lower()
        
        # Count occurrences of different severity levels
        mild_count = sum(1 for word in mild_toxic if word in content_lower)
        moderate_count = sum(1 for word in moderate_toxic if word in content_lower)
        severe_count = sum(1 for word in severe_toxic if word in content_lower)
        
        # Calculate weighted toxicity score
        total_score = (mild_count * 0.1) + (moderate_count * 0.3) + (severe_count * 0.5)
        
        # More nuanced scoring to properly distribute across protection levels
        if total_score == 0:
            return 0.05  # Very clean baseline
        elif total_score <= 0.15:  # 1 mild word
            return 0.35  # Minor toxicity -> FORWARD_WITH_CONTEXT
        elif total_score <= 0.65:  # 1-2 moderate words or multiple mild
            return 0.65  # Moderate toxicity -> REDACT_HARMFUL
        elif total_score <= 0.9:  # 3 moderate words
            return 0.85  # High toxicity -> SUMMARIZE_ONLY
        else:  # Severe words or many moderate words (>0.9)
            return 0.95  # Extreme toxicity -> BLOCK_ENTIRELY
    
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
                import re
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