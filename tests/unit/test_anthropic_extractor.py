"""Tests for AnthropicExtractor — RED phase.

Tests the production entity extractor that calls the Anthropic API.
All tests mock the Anthropic client to avoid real API calls.
"""

import json
import time

import pytest

from cellophanemail.features.entity_extraction.anthropic_extractor import (
    AnthropicExtractor,
)
from cellophanemail.features.entity_extraction.extractor_interface import (
    IEntityExtractor,
)
from cellophanemail.features.entity_extraction.types import (
    EntityType,
    ExtractionResult,
    Tone,
)


class TestAnthropicExtractorInterface:
    """AnthropicExtractor must implement IEntityExtractor."""

    def test_is_instance_of_interface(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        assert isinstance(extractor, IEntityExtractor)


class TestAnthropicExtractorPromptBuilding:
    """Prompt sent to the API must request JSON with entity schema."""

    def test_prompt_includes_entity_types(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        prompt = extractor._build_prompt("Hello Sarah", channel="sms")
        assert "person_name" in prompt
        assert "location" in prompt
        assert "url" in prompt
        assert "email" in prompt
        assert "phone_number" in prompt

    def test_prompt_includes_tone_values(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        prompt = extractor._build_prompt("Hello", channel="sms")
        assert "warm" in prompt
        assert "formal" in prompt
        assert "casual" in prompt

    def test_prompt_includes_content(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        prompt = extractor._build_prompt("Meet Sarah at the park", channel="sms")
        assert "Meet Sarah at the park" in prompt

    def test_prompt_includes_channel(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        prompt = extractor._build_prompt("hello", channel="email")
        assert "email" in prompt

    def test_prompt_requests_json(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        prompt = extractor._build_prompt("hello", channel="sms")
        assert "JSON" in prompt


class TestAnthropicExtractorResponseParsing:
    """Parse LLM JSON response into ExtractionResult."""

    def test_parse_valid_response(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        content = "Tell Sarah I'm at the park"
        response = json.dumps({
            "entities": [
                {"text": "Sarah", "type": "person_name", "confidence": 0.95},
                {"text": "the park", "type": "location", "confidence": 0.8},
            ],
            "tone": "casual",
        })
        result = extractor._parse_response(response, content)
        assert isinstance(result, ExtractionResult)
        assert len(result.entities) == 2
        assert result.tone == Tone.CASUAL

    def test_parse_entities_have_positions(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        content = "Sarah said hello"
        response = json.dumps({
            "entities": [
                {"text": "Sarah", "type": "person_name", "confidence": 0.9},
            ],
            "tone": "casual",
        })
        result = extractor._parse_response(response, content)
        assert result.entities[0].start == 0
        assert result.entities[0].end == 5
        assert content[result.entities[0].start : result.entities[0].end] == "Sarah"

    def test_parse_handles_markdown_code_block(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        content = "Hello Bob"
        response = '```json\n{"entities": [{"text": "Bob", "type": "person_name", "confidence": 0.9}], "tone": "casual"}\n```'
        result = extractor._parse_response(response, content)
        assert len(result.entities) == 1
        assert result.entities[0].text == "Bob"

    def test_parse_empty_entities(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        response = json.dumps({"entities": [], "tone": "casual"})
        result = extractor._parse_response(response, "nothing here")
        assert result.entities == []
        assert result.tone == Tone.CASUAL

    def test_parse_null_tone(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        response = json.dumps({"entities": [], "tone": None})
        result = extractor._parse_response(response, "hello")
        assert result.tone is None

    def test_parse_unknown_entity_type_skipped(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        content = "Sarah at NASA"
        response = json.dumps({
            "entities": [
                {"text": "Sarah", "type": "person_name", "confidence": 0.9},
                {"text": "NASA", "type": "alien_base", "confidence": 0.5},
            ],
            "tone": "casual",
        })
        result = extractor._parse_response(response, content)
        # Only valid entity types survive
        assert len(result.entities) == 1
        assert result.entities[0].text == "Sarah"

    def test_parse_malformed_json_raises(self):
        extractor = AnthropicExtractor(api_key="sk-test-fake")
        with pytest.raises(RuntimeError, match="parse"):
            extractor._parse_response("not json at all {{{", "hello")


class TestAnthropicExtractorEndToEnd:
    """Full extract_entities flow with mocked Anthropic client."""

    @pytest.mark.anyio
    async def test_extract_entities_calls_api(self, mocker):
        extractor = AnthropicExtractor(api_key="sk-test-fake")

        # Mock the Anthropic client
        mock_response = mocker.MagicMock()
        mock_response.content = [
            mocker.MagicMock(
                text=json.dumps({
                    "entities": [
                        {"text": "Sarah", "type": "person_name", "confidence": 0.95},
                    ],
                    "tone": "warm",
                })
            )
        ]
        mock_client = mocker.MagicMock()
        mock_client.messages.create.return_value = mock_response
        extractor._client = mock_client

        result = await extractor.extract_entities("Tell Sarah hi")
        assert isinstance(result, ExtractionResult)
        assert len(result.entities) == 1
        assert result.entities[0].text == "Sarah"
        assert result.tone == Tone.WARM
        assert result.extractor_used == "anthropic"
        assert result.processing_time_ms >= 0

    @pytest.mark.anyio
    async def test_extract_entities_empty_content(self, mocker):
        extractor = AnthropicExtractor(api_key="sk-test-fake")

        mock_response = mocker.MagicMock()
        mock_response.content = [
            mocker.MagicMock(
                text=json.dumps({"entities": [], "tone": None})
            )
        ]
        mock_client = mocker.MagicMock()
        mock_client.messages.create.return_value = mock_response
        extractor._client = mock_client

        result = await extractor.extract_entities("")
        assert result.entities == []

    @pytest.mark.anyio
    async def test_api_error_raises_runtime_error(self, mocker):
        extractor = AnthropicExtractor(api_key="sk-test-fake")

        mock_client = mocker.MagicMock()
        mock_client.messages.create.side_effect = Exception("API rate limit")
        extractor._client = mock_client

        with pytest.raises(RuntimeError, match="Entity extraction failed"):
            await extractor.extract_entities("hello")
