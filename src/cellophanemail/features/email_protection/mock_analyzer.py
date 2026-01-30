"""
Mock email analyzer for testing.
Provides deterministic responses without API calls.
"""

import logging
from typing import List
from dataclasses import dataclass
from .analyzer_interface import IEmailAnalyzer
from .models import ThreatLevel, HorsemanDetection

logger = logging.getLogger(__name__)


@dataclass
class EmailAnalysis:
    """Email analysis result - compatible with EmailToxicityAnalyzer."""
    threat_level: ThreatLevel
    safe: bool
    horsemen_detected: List[HorsemanDetection]
    reasoning: str
    confidence: float
    processing_time_ms: int
    language_detected: str = "en"


class MockAnalyzer(IEmailAnalyzer):
    """
    Mock email analyzer for testing.
    Returns predefined responses without making API calls.
    """

    def __init__(self):
        """Initialize mock analyzer with default responses."""
        self.call_count = 0
        self.call_history = []
        self.custom_responses = {}
        self.fact_responses = {}

    def set_horsemen_response(
        self,
        email_pattern: str,
        horsemen: List[HorsemanDetection],
        safe: bool = True
    ):
        """
        Set custom response for specific email patterns.

        Args:
            email_pattern: Pattern to match in email content (simple substring)
            horsemen: List of horsemen to detect
            safe: Whether email is considered safe
        """
        self.custom_responses[email_pattern.lower()] = {
            "horsemen": horsemen,
            "safe": safe
        }

    def set_fact_response(self, fact_pattern: str, presentation: str):
        """
        Set response for fact presentation analysis.

        Args:
            fact_pattern: Pattern to match in fact text
            presentation: "positive", "neutral", or "negative"
        """
        self.fact_responses[fact_pattern.lower()] = presentation

    def analyze_email_toxicity(self, email_content: str, sender_email: str) -> EmailAnalysis:
        """
        Mock email toxicity analysis with predictable responses.
        """
        self.call_count += 1
        self.call_history.append({
            "method": "analyze_email_toxicity",
            "content": email_content[:100] + "..." if len(email_content) > 100 else email_content,
            "sender": sender_email
        })

        # Check for custom responses based on content patterns
        content_lower = email_content.lower()
        for pattern, response in self.custom_responses.items():
            if pattern in content_lower:
                horsemen = response["horsemen"]
                threat_level = ThreatLevel.from_horsemen(horsemen)
                logger.info(f"MockAnalyzer: Found pattern '{pattern}', returning threat_level {threat_level.value}")
                return EmailAnalysis(
                    threat_level=threat_level,
                    safe=response["safe"],
                    horsemen_detected=horsemen,
                    reasoning=f"Mock analysis for pattern: {pattern}",
                    confidence=0.9,
                    processing_time_ms=10,  # Very fast mock response
                    language_detected="en"
                )

        # Default response - safe, no horsemen
        logger.info("MockAnalyzer: No custom pattern found, returning safe default")
        return EmailAnalysis(
            threat_level=ThreatLevel.SAFE,
            safe=True,
            horsemen_detected=[],
            reasoning="Mock analysis - default safe response",
            confidence=0.9,
            processing_time_ms=10,
            language_detected="en"
        )

    def analyze_fact_presentation(self, fact_text: str, full_email_content: str, sender_email: str) -> str:
        """
        Mock fact presentation analysis.
        """
        self.call_count += 1
        self.call_history.append({
            "method": "analyze_fact_presentation",
            "fact": fact_text,
            "sender": sender_email
        })

        # Check for custom responses
        fact_lower = fact_text.lower()
        for pattern, response in self.fact_responses.items():
            if pattern in fact_lower:
                return response

        # Default to neutral
        return "neutral"

    def reset(self):
        """Reset call history and custom responses."""
        self.call_count = 0
        self.call_history.clear()
        self.custom_responses.clear()
        self.fact_responses.clear()


# Predefined mock analyzers for common test scenarios
def create_clean_analyzer() -> MockAnalyzer:
    """Create analyzer that always returns clean/safe results."""
    return MockAnalyzer()


def create_toxic_analyzer() -> MockAnalyzer:
    """Create analyzer that returns appropriate horsemen for typical toxic content."""
    mock = MockAnalyzer()

    # Critical: Contempt + other horsemen
    mock.set_horsemen_response(
        "hate",
        [
            HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["hate"], severity="high"),
            HorsemanDetection(horseman="criticism", confidence=0.8, indicators=["character attack"], severity="high"),
        ],
        safe=False
    )
    mock.set_horsemen_response(
        "worthless",
        [
            HorsemanDetection(horseman="contempt", confidence=0.95, indicators=["worthless"], severity="high"),
            HorsemanDetection(horseman="criticism", confidence=0.9, indicators=["character attack"], severity="high"),
        ],
        safe=False
    )
    mock.set_horsemen_response(
        "hunt you down",
        [
            HorsemanDetection(horseman="contempt", confidence=0.95, indicators=["threat"], severity="high"),
            HorsemanDetection(horseman="criticism", confidence=0.8, indicators=["attack"], severity="high"),
        ],
        safe=False
    )
    mock.set_horsemen_response(
        "make you pay",
        [
            HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["threat"], severity="high"),
            HorsemanDetection(horseman="criticism", confidence=0.85, indicators=["attack"], severity="high"),
        ],
        safe=False
    )

    # High: Contempt alone
    mock.set_horsemen_response(
        "stupid idiot",
        [
            HorsemanDetection(horseman="contempt", confidence=0.85, indicators=["name-calling"], severity="high"),
        ],
        safe=False
    )
    mock.set_horsemen_response(
        "incompetent",
        [
            HorsemanDetection(horseman="contempt", confidence=0.8, indicators=["superiority"], severity="high"),
        ],
        safe=False
    )

    # Medium: 2 non-contempt horsemen
    mock.set_horsemen_response(
        "terrible",
        [
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["harsh judgment"], severity="medium"),
            HorsemanDetection(horseman="defensiveness", confidence=0.6, indicators=["blame-shifting"], severity="medium"),
        ],
        safe=False
    )
    mock.set_horsemen_response(
        "disappointing",
        [
            HorsemanDetection(horseman="criticism", confidence=0.65, indicators=["negative judgment"], severity="medium"),
            HorsemanDetection(horseman="stonewalling", confidence=0.55, indicators=["dismissive"], severity="medium"),
        ],
        safe=False
    )

    # Low: Single non-contempt horseman
    mock.set_horsemen_response(
        "too late",
        [
            HorsemanDetection(horseman="criticism", confidence=0.6, indicators=["time pressure"], severity="low"),
        ],
        safe=False
    )
    mock.set_horsemen_response(
        "should have done",
        [
            HorsemanDetection(horseman="criticism", confidence=0.55, indicators=["hindsight criticism"], severity="low"),
        ],
        safe=False
    )

    return mock


def create_graduated_analyzer() -> MockAnalyzer:
    """Create analyzer with graduated responses for threshold testing."""
    mock = MockAnalyzer()

    # LOW: Single non-contempt horseman
    mock.set_horsemen_response(
        "minor issue",
        [
            HorsemanDetection(horseman="criticism", confidence=0.6, indicators=["minor criticism"], severity="low"),
        ],
        safe=False
    )

    # MEDIUM: 2 non-contempt horsemen
    mock.set_horsemen_response(
        "moderate problem",
        [
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["criticism"], severity="medium"),
            HorsemanDetection(horseman="defensiveness", confidence=0.65, indicators=["defensiveness"], severity="medium"),
        ],
        safe=False
    )

    # HIGH: Contempt detected
    mock.set_horsemen_response(
        "serious issue",
        [
            HorsemanDetection(horseman="contempt", confidence=0.8, indicators=["mockery"], severity="high"),
        ],
        safe=False
    )

    # CRITICAL: Contempt + other horseman
    mock.set_horsemen_response(
        "extreme threat",
        [
            HorsemanDetection(horseman="contempt", confidence=0.95, indicators=["contempt"], severity="high"),
            HorsemanDetection(horseman="criticism", confidence=0.9, indicators=["attack"], severity="high"),
        ],
        safe=False
    )

    return mock
