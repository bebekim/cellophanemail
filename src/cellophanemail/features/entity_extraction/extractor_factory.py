"""ExtractorFactory — environment-based entity extractor selection.

Mirrors AnalyzerFactory from email_protection.
STAGING → MockExtractor, PRIVACY_MODE → (future) LlamaExtractor,
default → (future) AnthropicExtractor.
"""

import logging
import os
from typing import Optional

from .extractor_interface import IEntityExtractor

logger = logging.getLogger(__name__)

_TRUTHY = {"true", "1", "yes"}


class ExtractorFactory:
    """Factory for creating entity extractors based on environment."""

    @staticmethod
    def create_extractor(
        extractor_type: Optional[str] = None,
    ) -> IEntityExtractor:
        """Create extractor based on environment or explicit type.

        Args:
            extractor_type: Override environment detection ("mock", "anthropic").

        Returns:
            IEntityExtractor implementation.
        """
        if extractor_type:
            return ExtractorFactory._create_by_type(extractor_type)

        if os.getenv("STAGING", "").lower() in _TRUTHY:
            logger.info("Creating MockExtractor for staging environment")
            return ExtractorFactory._create_mock()

        if os.getenv("PRIVACY_MODE", "").lower() in _TRUTHY:
            logger.info("Creating MockExtractor (privacy placeholder)")
            return ExtractorFactory._create_mock()

        # Default: production (Anthropic) — not yet built, fall back to mock
        logger.info("Creating MockExtractor (production placeholder)")
        return ExtractorFactory._create_mock()

    @staticmethod
    def _create_by_type(extractor_type: str) -> IEntityExtractor:
        t = extractor_type.lower()
        if t == "mock":
            return ExtractorFactory._create_mock()
        raise ValueError(f"Unknown extractor type: {extractor_type}")

    @staticmethod
    def _create_mock() -> IEntityExtractor:
        from .mock_extractor import MockExtractor

        return MockExtractor()

    @staticmethod
    def detect_environment() -> str:
        """Detect current environment for logging."""
        if os.getenv("STAGING", "").lower() in _TRUTHY:
            return "staging"
        if os.getenv("PRIVACY_MODE", "").lower() in _TRUTHY:
            return "privacy"
        return "production"
