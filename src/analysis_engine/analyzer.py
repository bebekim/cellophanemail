# ABOUTME: Abstract analyzer interface for LLM backends
# ABOUTME: Implemented by Anthropic (cloud) and Llama (on-device)

from abc import ABC, abstractmethod

from .types import AnalysisResult


class IAnalyzer(ABC):
    """
    Abstract interface for content analysis.

    Implementations:
    - AnthropicAnalyzer (cloud API) - for CellophoneMail web
    - LlamaAnalyzer (on-device) - for Android app offline mode
    - MockAnalyzer (testing) - for unit tests
    """

    @abstractmethod
    async def analyze(self, content: str, sender: str = "") -> AnalysisResult:
        """
        Analyze content for Four Horseman patterns.

        Args:
            content: Text content to analyze (email body, SMS, etc.)
            sender: Optional sender identifier for context

        Returns:
            AnalysisResult with toxicity assessment
        """
        pass

    @abstractmethod
    async def rephrase(self, content: str, analysis: AnalysisResult) -> str:
        """
        Rephrase toxic content to be less harmful.

        Args:
            content: Original toxic content
            analysis: Analysis result with detected patterns

        Returns:
            Rephrased content with toxicity removed
        """
        pass
