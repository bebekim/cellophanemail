"""AnthropicExtractor — production entity extraction via Claude API.

Mirrors EmailToxicityAnalyzer pattern: lazy client init, structured prompt,
JSON response parsing with repair, IndexResolver for positions.
"""

import json
import logging
import re
import time
from typing import Optional

from .extractor_interface import IEntityExtractor
from .index_resolver import IndexResolver
from .types import ExtractionResult, Tone

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-5-20250929"
_MAX_TOKENS = 800


class AnthropicExtractor(IEntityExtractor):
    """Entity extractor using Anthropic Claude API."""

    def __init__(
        self,
        api_key: str,
        model: str = _MODEL,
        temperature: float = 0.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._client: Optional[object] = None

    def _ensure_client(self) -> None:
        """Lazy-init Anthropic client on first use."""
        if self._client is not None:
            return
        import anthropic

        self._client = anthropic.Anthropic(api_key=self._api_key)

    def _build_prompt(self, content: str, channel: str = "sms") -> str:
        """Build extraction prompt requesting JSON output."""
        return f"""Extract named entities and detect tone from the following {channel} message. Output ONLY valid JSON, no other text.

Message:
{content}

Extract these entity types (only include entities actually present):
- person_name: Names of people
- location: Places, addresses, landmarks
- organization: Companies, institutions, groups
- date_time: Dates, times, durations
- url: Web URLs
- email: Email addresses
- phone_number: Phone numbers

Detect the overall tone (pick one):
- warm: Friendly, affectionate
- formal: Professional, polite
- casual: Relaxed, informal
- contemplative: Reflective, thoughtful
- urgent: Time-sensitive, alarming

Output this exact JSON structure:
{{"entities": [{{"text": "exact text from message", "type": "entity_type", "confidence": 0.0}}], "tone": "tone_value"}}"""

    def _extract_json(self, response: str) -> str:
        """Extract JSON from response, handling markdown code blocks."""
        code_block = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
        )
        if code_block:
            return code_block.group(1)

        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            return json_match.group(0)

        return response

    def _parse_response(self, response: str, content: str) -> ExtractionResult:
        """Parse LLM JSON response into ExtractionResult with positions."""
        from json_repair import repair_json

        try:
            json_str = self._extract_json(response)
            repaired = repair_json(json_str)
            data = json.loads(repaired)
            if not isinstance(data, dict):
                raise ValueError("Expected JSON object, got " + type(data).__name__)
        except (json.JSONDecodeError, ValueError) as e:
            raise RuntimeError(f"Failed to parse LLM response: {e}")

        raw_entities = data.get("entities", [])

        # Resolve positions via IndexResolver (skips unknown types)
        entities = IndexResolver.resolve(content, raw_entities)

        # Parse tone
        tone_str = data.get("tone")
        tone: Optional[Tone] = None
        if tone_str:
            try:
                tone = Tone(tone_str)
            except ValueError:
                pass

        return ExtractionResult(
            entities=entities,
            tone=tone,
            extractor_used="anthropic",
        )

    async def extract_entities(
        self, content: str, channel: str = "sms"
    ) -> ExtractionResult:
        """Extract entities from content via Anthropic API."""
        start_time = time.monotonic()

        try:
            self._ensure_client()
            prompt = self._build_prompt(content, channel)

            response = self._client.messages.create(
                model=self._model,
                max_tokens=_MAX_TOKENS,
                temperature=self._temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text.strip()

            result = self._parse_response(response_text, content)
            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            return ExtractionResult(
                entities=result.entities,
                tone=result.tone,
                processing_time_ms=elapsed_ms,
                extractor_used="anthropic",
            )
        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            raise RuntimeError(f"Entity extraction failed: {e}")
