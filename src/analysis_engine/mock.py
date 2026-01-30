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
        default_safe: bool = True,
        rephrase_prefix: str = "[Rephrased] ",
    ):
        """
        Initialize mock analyzer with configurable defaults.

        Args:
            default_safe: Default safe flag when no custom response matches
            rephrase_prefix: Prefix added to rephrased content
        """
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
            AnalysisResult with mock analysis based on horsemen detection
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
                horsemen = response.get("horsemen", [])
                reasoning = response.get("reasoning")
                if reasoning is None:
                    reasoning = f"Mock: matched pattern '{pattern}'"

                # Derive threat level from horsemen
                threat_level = ThreatLevel.from_horsemen(horsemen)
                safe = threat_level == ThreatLevel.SAFE

                return AnalysisResult(
                    safe=safe,
                    threat_level=threat_level,
                    horsemen_detected=horsemen,
                    reasoning=reasoning,
                    processing_time_ms=1,
                    cached=False,
                )

        # Default response - no horsemen = safe
        return AnalysisResult(
            safe=self.default_safe,
            threat_level=ThreatLevel.SAFE if self.default_safe else ThreatLevel.LOW,
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
            "threat_level": analysis.threat_level.value,
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
        horsemen: List[HorsemanDetection],
        safe: bool = False,
        reasoning: Optional[str] = None,
    ) -> None:
        """
        Set custom response for content matching a pattern.

        Args:
            pattern: Substring to match in content (case-insensitive)
            horsemen: List of horsemen detections (threat level derived from these)
            safe: Whether content is considered safe (override)
            reasoning: Custom reasoning text
        """
        self.custom_responses[pattern.lower()] = {
            "horsemen": horsemen,
            "safe": safe,
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
    return MockAnalyzer(default_safe=True)


def create_toxic_analyzer() -> MockAnalyzer:
    """
    Create analyzer with common toxic patterns pre-configured.

    Uses horsemen-based detection (contempt-weighted):
    - CRITICAL: Contempt + other horseman
    - HIGH: Contempt alone
    - MEDIUM: 2 non-contempt horsemen
    - LOW: Single non-contempt horseman
    """
    mock = MockAnalyzer(default_safe=True)

    # Critical: Contempt + other horsemen
    for pattern in ["hate", "worthless", "hunt you down", "make you pay", "you'll regret", "threatening"]:
        mock.set_response(
            pattern,
            horsemen=[
                HorsemanDetection(horseman="contempt", confidence=0.9, indicators=[pattern], severity="high"),
                HorsemanDetection(horseman="criticism", confidence=0.8, indicators=["attack"], severity="high"),
            ],
            safe=False
        )

    # High: Contempt alone
    for pattern in ["stupid idiot", "incompetent", "sick of dealing"]:
        mock.set_response(
            pattern,
            horsemen=[
                HorsemanDetection(horseman="contempt", confidence=0.85, indicators=[pattern], severity="high"),
            ],
            safe=False
        )

    # Medium: 2 non-contempt horsemen
    for pattern in ["terrible", "disappointing", "awful"]:
        mock.set_response(
            pattern,
            horsemen=[
                HorsemanDetection(horseman="criticism", confidence=0.7, indicators=[pattern], severity="medium"),
                HorsemanDetection(horseman="defensiveness", confidence=0.6, indicators=["blame"], severity="medium"),
            ],
            safe=False
        )

    # Low: Single non-contempt horseman
    for pattern in ["too late", "time is running out", "should have"]:
        mock.set_response(
            pattern,
            horsemen=[
                HorsemanDetection(horseman="criticism", confidence=0.6, indicators=[pattern], severity="low"),
            ],
            safe=False
        )

    return mock


def create_graduated_analyzer() -> MockAnalyzer:
    """
    Create analyzer with explicit graduated responses for threshold testing.

    Uses horsemen-based detection:
    - "minor issue" → LOW (single non-contempt horseman)
    - "moderate problem" → MEDIUM (2 non-contempt horsemen)
    - "serious issue" → HIGH (contempt alone)
    - "extreme threat" → CRITICAL (contempt + other horseman)
    """
    mock = MockAnalyzer(default_safe=True)

    mock.set_response(
        "minor issue",
        horsemen=[
            HorsemanDetection(horseman="criticism", confidence=0.6, indicators=["minor"], severity="low"),
        ],
        safe=False
    )

    mock.set_response(
        "moderate problem",
        horsemen=[
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["moderate"], severity="medium"),
            HorsemanDetection(horseman="defensiveness", confidence=0.65, indicators=["problem"], severity="medium"),
        ],
        safe=False
    )

    mock.set_response(
        "serious issue",
        horsemen=[
            HorsemanDetection(horseman="contempt", confidence=0.8, indicators=["serious"], severity="high"),
        ],
        safe=False
    )

    mock.set_response(
        "extreme threat",
        horsemen=[
            HorsemanDetection(horseman="contempt", confidence=0.95, indicators=["extreme"], severity="high"),
            HorsemanDetection(horseman="criticism", confidence=0.9, indicators=["threat"], severity="high"),
        ],
        safe=False
    )

    return mock
