"""Tests for MockExtractor — RED phase.

These tests define the contract for MockExtractor before implementation exists.
Mirrors the test pattern from test_mock_analyzer.py.
"""

import pytest

from cellophanemail.features.entity_extraction.extractor_interface import (
    IEntityExtractor,
)
from cellophanemail.features.entity_extraction.mock_extractor import MockExtractor
from cellophanemail.features.entity_extraction.types import (
    EntityType,
    ExtractionResult,
    Tone,
)


class TestMockExtractorInterface:
    """MockExtractor must implement IEntityExtractor."""

    def test_is_instance_of_interface(self):
        mock = MockExtractor()
        assert isinstance(mock, IEntityExtractor)

    @pytest.mark.anyio
    async def test_extract_entities_is_async(self):
        mock = MockExtractor()
        result = await mock.extract_entities("hello")
        assert isinstance(result, ExtractionResult)


class TestMockExtractorDefaults:
    """Default behavior: deterministic entity extraction from known patterns."""

    @pytest.mark.anyio
    async def test_default_returns_extraction_result(self):
        mock = MockExtractor()
        result = await mock.extract_entities("no entities here")
        assert isinstance(result, ExtractionResult)
        assert result.extractor_used == "mock"

    @pytest.mark.anyio
    async def test_default_empty_content(self):
        mock = MockExtractor()
        result = await mock.extract_entities("")
        assert result.entities == []

    @pytest.mark.anyio
    async def test_detects_person_names(self):
        """Known person name patterns are detected."""
        mock = MockExtractor()
        result = await mock.extract_entities("Tell Sarah I said hi")
        names = [e for e in result.entities if e.type == EntityType.PERSON_NAME]
        assert len(names) >= 1
        assert names[0].text == "Sarah"

    @pytest.mark.anyio
    async def test_detects_urls(self):
        mock = MockExtractor()
        result = await mock.extract_entities("Visit https://example.com today")
        urls = [e for e in result.entities if e.type == EntityType.URL]
        assert len(urls) == 1
        assert urls[0].text == "https://example.com"

    @pytest.mark.anyio
    async def test_detects_emails(self):
        mock = MockExtractor()
        result = await mock.extract_entities("Contact bob@example.com for info")
        emails = [e for e in result.entities if e.type == EntityType.EMAIL]
        assert len(emails) == 1
        assert emails[0].text == "bob@example.com"

    @pytest.mark.anyio
    async def test_detects_phone_numbers(self):
        mock = MockExtractor()
        result = await mock.extract_entities("Call me at +1-555-867-5309")
        phones = [e for e in result.entities if e.type == EntityType.PHONE_NUMBER]
        assert len(phones) == 1
        assert "+1-555-867-5309" in phones[0].text

    @pytest.mark.anyio
    async def test_entities_have_valid_positions(self):
        """All entities have start/end that slice back to entity text."""
        mock = MockExtractor()
        content = "Email sarah@test.com or call +61412345678"
        result = await mock.extract_entities(content)
        for entity in result.entities:
            assert content[entity.start : entity.end] == entity.text

    @pytest.mark.anyio
    async def test_processing_time_is_set(self):
        mock = MockExtractor()
        result = await mock.extract_entities("Sarah said hello")
        assert result.processing_time_ms >= 0


class TestMockExtractorToneDetection:
    """MockExtractor should detect tone from content signals."""

    @pytest.mark.anyio
    async def test_urgent_tone(self):
        mock = MockExtractor()
        result = await mock.extract_entities("URGENT: Please respond ASAP!!!")
        assert result.tone == Tone.URGENT

    @pytest.mark.anyio
    async def test_formal_tone(self):
        mock = MockExtractor()
        result = await mock.extract_entities(
            "Dear Sir/Madam, I am writing to formally request"
        )
        assert result.tone == Tone.FORMAL

    @pytest.mark.anyio
    async def test_default_tone_is_casual(self):
        mock = MockExtractor()
        result = await mock.extract_entities("hey what's up")
        assert result.tone == Tone.CASUAL


class TestMockExtractorCustomResponses:
    """MockExtractor supports configurable responses for targeted testing."""

    @pytest.mark.anyio
    async def test_set_custom_response(self):
        mock = MockExtractor()
        custom = ExtractionResult(
            entities=[],
            tone=Tone.CONTEMPLATIVE,
            processing_time_ms=99,
            extractor_used="mock",
        )
        mock.set_response("meditation", custom)
        result = await mock.extract_entities("meditation is great")
        assert result.tone == Tone.CONTEMPLATIVE
        assert result.processing_time_ms == 99

    @pytest.mark.anyio
    async def test_custom_response_pattern_is_case_insensitive(self):
        mock = MockExtractor()
        custom = ExtractionResult(
            entities=[], tone=Tone.WARM, extractor_used="mock"
        )
        mock.set_response("HELLO", custom)
        result = await mock.extract_entities("hello world")
        assert result.tone == Tone.WARM


class TestMockExtractorCallTracking:
    """MockExtractor tracks calls for test assertions."""

    @pytest.mark.anyio
    async def test_call_count(self):
        mock = MockExtractor()
        assert mock.call_count == 0
        await mock.extract_entities("one")
        await mock.extract_entities("two")
        assert mock.call_count == 2

    @pytest.mark.anyio
    async def test_call_history(self):
        mock = MockExtractor()
        await mock.extract_entities("hello", channel="sms")
        await mock.extract_entities("world", channel="email")
        assert len(mock.call_history) == 2
        assert mock.call_history[0]["content"] == "hello"
        assert mock.call_history[0]["channel"] == "sms"
        assert mock.call_history[1]["content"] == "world"
        assert mock.call_history[1]["channel"] == "email"

    @pytest.mark.anyio
    async def test_reset(self):
        mock = MockExtractor()
        mock.set_response("x", ExtractionResult(extractor_used="mock"))
        await mock.extract_entities("test")
        mock.reset()
        assert mock.call_count == 0
        assert mock.call_history == []
