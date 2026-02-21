"""MockExtractor — deterministic entity extraction for testing.

Mirrors the MockAnalyzer pattern from email_protection.
Uses regex for URLs/emails/phones and a known-names list for person names.
No API calls. Configurable responses for targeted test scenarios.
"""

import re
import time
from typing import Optional

from .extractor_interface import IEntityExtractor
from .index_resolver import IndexResolver
from .types import EntityType, ExtractionResult, Tone


# Regex patterns for deterministic extraction
_URL_RE = re.compile(r"https?://[^\s,)>]+")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"\+?[\d][\d\s\-().]{6,}\d")

# Known names for mock detection (expandable)
_KNOWN_NAMES = {
    "Sarah", "Bob", "Alice", "John", "Jane", "David", "Emma", "Michael",
    "Lisa", "James", "Mary", "Robert", "Linda", "William", "Jennifer",
}

# Tone signal keywords
_TONE_SIGNALS: dict[Tone, list[str]] = {
    Tone.URGENT: ["urgent", "asap", "immediately", "emergency", "!!!"],
    Tone.FORMAL: ["dear sir", "dear madam", "formally", "sincerely", "regards"],
    Tone.WARM: ["love", "miss you", "thinking of you", "xoxo", "hugs"],
    Tone.CONTEMPLATIVE: ["wonder", "reflect", "ponder", "perhaps", "meditation"],
}


class MockExtractor(IEntityExtractor):
    """Deterministic entity extractor for testing and staging.

    Extracts entities via regex (URLs, emails, phones) and known-name
    matching (person names). Supports custom response overrides and
    call tracking for test assertions.
    """

    def __init__(self) -> None:
        self.call_count: int = 0
        self.call_history: list[dict] = []
        self._custom_responses: dict[str, ExtractionResult] = {}

    def set_response(self, pattern: str, result: ExtractionResult) -> None:
        """Set a custom response for content matching pattern (case-insensitive)."""
        self._custom_responses[pattern.lower()] = result

    def reset(self) -> None:
        """Reset call tracking and custom responses."""
        self.call_count = 0
        self.call_history.clear()
        self._custom_responses.clear()

    async def extract_entities(
        self, content: str, channel: str = "sms"
    ) -> ExtractionResult:
        start_time = time.monotonic()

        self.call_count += 1
        self.call_history.append({"content": content, "channel": channel})

        # Check custom responses first
        content_lower = content.lower()
        for pattern, response in self._custom_responses.items():
            if pattern in content_lower:
                return response

        if not content:
            return ExtractionResult(extractor_used="mock")

        # Build raw entities from regex + known names
        raw_entities = self._extract_raw(content)

        # Resolve positions via IndexResolver
        entities = IndexResolver.resolve(content, raw_entities)

        # Detect tone
        tone = self._detect_tone(content_lower)

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        return ExtractionResult(
            entities=entities,
            tone=tone,
            processing_time_ms=elapsed_ms,
            extractor_used="mock",
        )

    def _extract_raw(self, content: str) -> list[dict]:
        """Extract raw entity dicts from content using regex and known names."""
        raw: list[dict] = []

        for match in _URL_RE.finditer(content):
            raw.append(
                {"text": match.group(), "type": "url", "confidence": 0.95}
            )

        for match in _EMAIL_RE.finditer(content):
            # Skip if this text is part of a URL already found
            text = match.group()
            if any(text in r["text"] for r in raw):
                continue
            raw.append({"text": text, "type": "email", "confidence": 0.95})

        for match in _PHONE_RE.finditer(content):
            raw.append(
                {"text": match.group(), "type": "phone_number", "confidence": 0.9}
            )

        # Known names — word-boundary match
        for name in _KNOWN_NAMES:
            if re.search(rf"\b{re.escape(name)}\b", content):
                raw.append(
                    {"text": name, "type": "person_name", "confidence": 0.85}
                )

        return raw

    @staticmethod
    def _detect_tone(content_lower: str) -> Optional[Tone]:
        """Simple keyword-based tone detection."""
        for tone, signals in _TONE_SIGNALS.items():
            if any(signal in content_lower for signal in signals):
                return tone
        return Tone.CASUAL
