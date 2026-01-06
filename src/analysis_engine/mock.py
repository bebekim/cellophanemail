# ABOUTME: Mock analyzer for testing without LLM API calls
# ABOUTME: Configurable responses for different test scenarios

from typing import Dict, List, Optional

from .analyzer import IAnalyzer
from .types import AnalysisResult, HorsemanDetection, ThreatLevel


class MockAnalyzer(IAnalyzer):
    """
    Mock analyzer implementing IAnalyzer for testing.

    Provides deterministic responses without making LLM API calls.
    Useful for unit tests, integration tests, and offline development.
    """

    def __init__(
        self,
        default_toxicity: float = 0.1,
        default_safe: bool = True,
        rephrase_prefix: str = "[Rephrased] ",
    ):
        """
        Initialize mock analyzer with configurable defaults.

        Args:
            default_toxicity: Default toxicity score for all content (0.0-1.0)
            default_safe: Default safe flag when no custom response matches
            rephrase_prefix: Prefix added to rephrased content
        """
        self.default_toxicity = default_toxicity
        self.default_safe = default_safe
        self.rephrase_prefix = rephrase_prefix
        self.call_history: List[Dict] = []
        self.custom_responses: Dict[str, Dict] = {}
        self.custom_rephrases: Dict[str, str] = {}

    async def analyze(self, content: str, sender: str = "") -> AnalysisResult:
        """
        Mock analysis returning configurable results.

        Checks custom_responses for pattern matches, otherwise returns defaults.

        Args:
            content: Text content to analyze
            sender: Optional sender identifier

        Returns:
            AnalysisResult with mock toxicity assessment
        """
        self.call_history.append({
            "method": "analyze",
            "content": content[:100] + "..." if len(content) > 100 else content,
            "sender": sender,
        })

        # Check for custom responses based on content patterns
        content_lower = content.lower()
        for pattern, response in self.custom_responses.items():
            if pattern in content_lower:
                reasoning = response.get("reasoning")
                if reasoning is None:
                    reasoning = f"Mock: matched pattern '{pattern}'"
                return AnalysisResult(
                    safe=response.get("safe", self.default_safe),
                    threat_level=response.get(
                        "threat_level",
                        ThreatLevel.from_score(response.get("toxicity", self.default_toxicity))
                    ),
                    toxicity_score=response.get("toxicity", self.default_toxicity),
                    horsemen_detected=response.get("horsemen", []),
                    reasoning=reasoning,
                    processing_time_ms=1,
                    cached=False,
                )

        # Default response
        return AnalysisResult(
            safe=self.default_safe,
            threat_level=ThreatLevel.SAFE if self.default_safe else ThreatLevel.MEDIUM,
            toxicity_score=self.default_toxicity,
            horsemen_detected=[],
            reasoning="Mock analysis - default response",
            processing_time_ms=1,
            cached=False,
        )

    async def rephrase(self, content: str, analysis: AnalysisResult) -> str:
        """
        Mock rephrasing with configurable responses.

        Checks custom_rephrases for pattern matches, otherwise prefixes content.

        Args:
            content: Original content to rephrase
            analysis: Analysis result (used for context in custom rephrases)

        Returns:
            Mock rephrased content
        """
        self.call_history.append({
            "method": "rephrase",
            "content": content[:100] + "..." if len(content) > 100 else content,
            "toxicity_score": analysis.toxicity_score,
        })

        # Check for custom rephrase responses
        content_lower = content.lower()
        for pattern, rephrased in self.custom_rephrases.items():
            if pattern in content_lower:
                return rephrased

        # Default: prefix the content
        return f"{self.rephrase_prefix}{content}"

    def set_response(
        self,
        pattern: str,
        toxicity: float,
        safe: bool = False,
        threat_level: Optional[ThreatLevel] = None,
        horsemen: Optional[List[HorsemanDetection]] = None,
        reasoning: Optional[str] = None,
    ) -> None:
        """
        Set custom response for content matching a pattern.

        Args:
            pattern: Substring to match in content (case-insensitive)
            toxicity: Toxicity score to return (0.0-1.0)
            safe: Whether content is considered safe
            threat_level: Specific threat level (defaults to from_score)
            horsemen: List of horsemen detections to include
            reasoning: Custom reasoning text
        """
        self.custom_responses[pattern.lower()] = {
            "toxicity": toxicity,
            "safe": safe,
            "threat_level": threat_level or ThreatLevel.from_score(toxicity),
            "horsemen": horsemen or [],
            "reasoning": reasoning,
        }

    def set_rephrase(self, pattern: str, rephrased: str) -> None:
        """
        Set custom rephrase response for content matching a pattern.

        Args:
            pattern: Substring to match in content (case-insensitive)
            rephrased: Rephrased text to return
        """
        self.custom_rephrases[pattern.lower()] = rephrased

    def reset(self) -> None:
        """Reset call history and custom responses."""
        self.call_history.clear()
        self.custom_responses.clear()
        self.custom_rephrases.clear()

    @property
    def call_count(self) -> int:
        """Total number of analyze and rephrase calls."""
        return len(self.call_history)

    @property
    def analyze_calls(self) -> List[Dict]:
        """List of analyze calls made."""
        return [c for c in self.call_history if c["method"] == "analyze"]

    @property
    def rephrase_calls(self) -> List[Dict]:
        """List of rephrase calls made."""
        return [c for c in self.call_history if c["method"] == "rephrase"]


def create_clean_analyzer() -> MockAnalyzer:
    """Create analyzer that always returns clean/safe results."""
    return MockAnalyzer(default_toxicity=0.05, default_safe=True)


def create_toxic_analyzer() -> MockAnalyzer:
    """
    Create analyzer with common toxic patterns pre-configured.

    Patterns are configured to return appropriate toxicity levels:
    - Critical (0.95): threats, hate speech → BLOCK_ENTIRELY
    - High (0.85): severe insults → SUMMARIZE_ONLY
    - Medium (0.65): moderate hostility → REDACT_HARMFUL
    - Low (0.35): minor issues → FORWARD_WITH_CONTEXT
    """
    mock = MockAnalyzer(default_toxicity=0.05, default_safe=True)

    # Critical toxicity (0.95) → BLOCK_ENTIRELY
    for pattern in ["hate", "worthless", "hunt you down", "make you pay", "you'll regret", "threatening"]:
        mock.set_response(pattern, toxicity=0.95, safe=False)

    # High toxicity (0.85) → SUMMARIZE_ONLY
    for pattern in ["stupid idiot", "incompetent", "sick of dealing"]:
        mock.set_response(pattern, toxicity=0.85, safe=False)

    # Medium toxicity (0.65) → REDACT_HARMFUL
    for pattern in ["terrible", "disappointing", "awful"]:
        mock.set_response(pattern, toxicity=0.65, safe=False)

    # Low toxicity (0.35) → FORWARD_WITH_CONTEXT
    for pattern in ["too late", "time is running out", "should have"]:
        mock.set_response(pattern, toxicity=0.35, safe=False)

    return mock


def create_graduated_analyzer() -> MockAnalyzer:
    """
    Create analyzer with explicit graduated responses for threshold testing.

    Returns specific toxicity scores for test patterns:
    - "minor issue" → 0.35 (FORWARD_WITH_CONTEXT)
    - "moderate problem" → 0.65 (REDACT_HARMFUL)
    - "serious issue" → 0.85 (SUMMARIZE_ONLY)
    - "extreme threat" → 0.95 (BLOCK_ENTIRELY)
    """
    mock = MockAnalyzer(default_toxicity=0.05, default_safe=True)

    mock.set_response("minor issue", toxicity=0.35, safe=False)
    mock.set_response("moderate problem", toxicity=0.65, safe=False)
    mock.set_response("serious issue", toxicity=0.85, safe=False)
    mock.set_response("extreme threat", toxicity=0.95, safe=False)

    return mock
