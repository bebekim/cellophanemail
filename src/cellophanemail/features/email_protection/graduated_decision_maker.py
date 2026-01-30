"""
Graduated Decision Maker for sophisticated email protection decisions.

Uses analysis_engine for core scoring logic, adds cellophanemail-specific
content processing (redaction, summarization, context notes).

Actions based on Four Horsemen detection (contempt-weighted):
- FORWARD_CLEAN: No significant horsemen detected
- FORWARD_WITH_CONTEXT: Single non-contempt horseman
- REDACT_HARMFUL: 2 non-contempt horsemen
- SUMMARIZE_ONLY: Contempt detected, OR 3+ non-contempt horsemen
- BLOCK_ENTIRELY: Contempt + any other horseman, OR all 4 horsemen
"""

import re
from dataclasses import dataclass
from typing import Optional

# Import core types from portable analysis_engine
from analysis_engine import (
    ProtectionAction,
    decide_action,
    AnalysisResult,
    ThreatLevel,
)


@dataclass
class ProtectionDecision:
    """Decision made by the graduated decision maker."""

    action: ProtectionAction
    processed_content: str
    reasoning: str
    threat_level: ThreatLevel
    original_analysis: Optional[AnalysisResult] = None


class GraduatedDecisionMaker:
    """
    Makes graduated protection decisions based on Four Horsemen detection.

    Uses analysis_engine.decide_action() for core decision logic,
    adds cellophanemail-specific content processing.
    """

    def __init__(self):
        """Initialize the decision maker."""
        pass

    def make_decision(self, analysis: AnalysisResult, original_content: str) -> ProtectionDecision:
        """
        Make a graduated protection decision based on analysis results.

        Args:
            analysis: The analysis result with horsemen detections
            original_content: The original email content

        Returns:
            ProtectionDecision with action and processed content
        """
        # Use analysis_engine's decide_action for core logic
        action = decide_action(analysis.horsemen_detected)
        threat_level = analysis.threat_level

        # Apply cellophanemail-specific content processing based on action
        if action == ProtectionAction.FORWARD_CLEAN:
            processed_content = original_content
            reasoning = f"Clean content (threat_level: {threat_level.value})"

        elif action == ProtectionAction.FORWARD_WITH_CONTEXT:
            processed_content = self._add_context_notes(original_content, analysis)
            # Include specific horsemen in reasoning if detected
            horsemen_names = [h.horseman for h in analysis.horsemen_detected] if analysis.horsemen_detected else []
            if horsemen_names:
                reasoning = f"Minor concern with {', '.join(horsemen_names)} detected (threat_level: {threat_level.value}) - adding context"
            else:
                reasoning = f"Minor concern detected (threat_level: {threat_level.value}) - adding context"

        elif action == ProtectionAction.REDACT_HARMFUL:
            processed_content = self._redact_harmful_content(original_content, analysis)
            reasoning = f"Moderate toxicity (threat_level: {threat_level.value}) - redacting harmful content"

        elif action == ProtectionAction.SUMMARIZE_ONLY:
            processed_content = self._create_summary(original_content, analysis)
            reasoning = f"High toxicity (threat_level: {threat_level.value}) - providing factual summary only"

        else:  # BLOCK_ENTIRELY
            processed_content = ""
            reasoning = f"Extreme toxicity (threat_level: {threat_level.value}) - blocking entirely"

        return ProtectionDecision(
            action=action,
            processed_content=processed_content,
            reasoning=reasoning,
            threat_level=threat_level,
            original_analysis=analysis,
        )

    def _add_context_notes(self, content: str, analysis: AnalysisResult) -> str:
        """Add helpful context notes to content with minor concerns."""
        context_notes = []

        # Add context based on detected horsemen
        if analysis.horsemen_detected:
            for horseman in analysis.horsemen_detected:
                if horseman.horseman == "criticism":
                    context_notes.append("criticism patterns detected")
                elif horseman.horseman == "contempt":
                    context_notes.append("contempt patterns detected")
                elif horseman.horseman == "defensiveness":
                    context_notes.append("defensive language present")
                elif horseman.horseman == "stonewalling":
                    context_notes.append("withdrawal patterns detected")

        if not context_notes:
            context_notes.append("minor concerning patterns detected")

        context_note = "[CONTEXT: This message contains " + ", ".join(context_notes) + "]"

        return f"{content}\n\n{context_note}"

    def _redact_harmful_content(self, content: str, analysis: AnalysisResult) -> str:
        """Redact harmful parts while preserving factual information."""
        # Simple redaction strategy - remove obviously harmful words
        harmful_patterns = [
            r'\b(terrible|awful|horrible|disgusting|pathetic|worthless|stupid|idiot|incompetent)\b',
            r'\b(hate|despise|loathe)\s+you\b',
            r'\byou\'?re\s+(a\s+)?(terrible|awful|horrible|disgusting|pathetic|worthless|stupid|idiot|incompetent)\b'
        ]

        processed = content
        redacted_count = 0

        for pattern in harmful_patterns:
            matches = re.findall(pattern, processed, re.IGNORECASE)
            if matches:
                processed = re.sub(pattern, '[REDACTED]', processed, flags=re.IGNORECASE)
                redacted_count += len(matches)

        if redacted_count > 0:
            processed += f"\n\n[NOTE: {redacted_count} harmful expressions were redacted]"

        return processed

    def _create_summary(self, content: str, analysis: AnalysisResult) -> str:
        """Create a factual-only summary of the content."""
        # Extract factual information while avoiding harmful content
        factual_extracts = []

        # Patterns for factual information with capture groups
        factual_patterns = [
            (r'\b(meeting\s+(?:is\s+)?at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)?)\b', 1),  # Meeting times
            (r'\b(deadline\s+(?:is\s+)?(?:by\s+)?\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b', 1),  # Deadlines
            (r'\b(please\s+send\s+(?:the\s+)?(?:report|invoice|document)(?:\s+by\s+\w+)?)\b', 1),  # Requests
            (r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)(?:\s+(?:tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday))?)\b', 1),  # Times
        ]

        # Look for sentences that contain factual information but remove harmful parts
        sentences = re.split(r'[.!?]+', content)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if sentence contains factual patterns
            for pattern, group in factual_patterns:
                matches = re.findall(pattern, sentence, re.IGNORECASE)
                if matches:
                    for match in matches:
                        factual_extracts.append(match)

            # Also extract common business/factual phrases
            business_patterns = [
                r'\b(meeting\s+is\s+at\s+\d{1,2}(?:am|pm)?\s*(?:tomorrow|today)?)\b',
                r'\b(report\s+(?:by|on)\s+\w+)\b',
                r'\b(invoice\s+\w+)\b',
                r'\b(project\s+\w+)\b'
            ]

            for pattern in business_patterns:
                matches = re.findall(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    factual_extracts.append(match)

        # Also look for standalone factual information
        standalone_facts = []
        if re.search(r'\b\d{1,2}(?:am|pm)\b', content, re.IGNORECASE):
            time_matches = re.findall(r'\b(\d{1,2}(?:am|pm))\b', content, re.IGNORECASE)
            standalone_facts.extend(time_matches)

        if re.search(r'\bmeet(?:ing)?\b', content, re.IGNORECASE):
            meeting_context = re.findall(r'(meeting\s+(?:is\s+)?at\s+\d{1,2}(?:am|pm)?(?:\s+\w+)?)', content, re.IGNORECASE)
            standalone_facts.extend(meeting_context)

        all_facts = factual_extracts + standalone_facts

        if all_facts:
            # Remove duplicates and create summary
            unique_facts = list(set(all_facts))
            summary = "[SUMMARY: Factual content only]\n" + "\n".join(unique_facts)
        else:
            summary = "[SUMMARY: No clear factual information could be safely extracted]"

        return summary
