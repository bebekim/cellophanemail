"""Interface for entity extractors.

Mirrors the pattern from email_protection/analyzer_interface.py.
All extractors (Anthropic, Llama, Mock) must implement this interface.
"""

from abc import ABC, abstractmethod

from .types import ExtractionResult


class IEntityExtractor(ABC):
    """Interface for entity extractors."""

    @abstractmethod
    async def extract_entities(
        self, content: str, channel: str = "sms"
    ) -> ExtractionResult:
        """Extract named entities from content.

        Args:
            content: Text content to extract entities from.
            channel: Message channel (sms, email, chat).

        Returns:
            ExtractionResult with extracted entities, tone, and metadata.
        """
