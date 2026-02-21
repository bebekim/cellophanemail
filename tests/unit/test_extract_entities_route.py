"""Tests for entity extraction endpoint DTOs and response shaping — RED phase."""

import pytest
from pydantic import ValidationError

from cellophanemail.routes.messages import (
    EntityExtractRequest,
    EntityExtractResponse,
    ExtractedEntityDTO,
    MessageChannel,
)
from cellophanemail.features.entity_extraction.types import (
    EntityType,
    ExtractionResult,
    ExtractedEntity,
    Tone,
)


class TestEntityExtractRequest:
    """Request DTO validation."""

    def test_valid_minimal(self):
        req = EntityExtractRequest(content="Hello Sarah")
        assert req.content == "Hello Sarah"
        assert req.channel == MessageChannel.OTHER

    def test_valid_with_channel(self):
        req = EntityExtractRequest(content="hi", channel=MessageChannel.SMS)
        assert req.channel == MessageChannel.SMS

    def test_rejects_empty_content(self):
        with pytest.raises(ValidationError):
            EntityExtractRequest(content="")

    def test_rejects_missing_content(self):
        with pytest.raises(ValidationError):
            EntityExtractRequest()

    def test_content_max_length(self):
        EntityExtractRequest(content="x" * 50000)
        with pytest.raises(ValidationError):
            EntityExtractRequest(content="x" * 50001)


class TestExtractedEntityDTO:
    """Response entity DTO."""

    def test_valid_entity(self):
        dto = ExtractedEntityDTO(
            text="Sarah",
            type="person_name",
            start=0,
            end=5,
            confidence=0.95,
        )
        assert dto.text == "Sarah"
        assert dto.start == 0
        assert dto.end == 5

    def test_confidence_bounds(self):
        ExtractedEntityDTO(text="x", type="url", start=0, end=1, confidence=0.0)
        ExtractedEntityDTO(text="x", type="url", start=0, end=1, confidence=1.0)
        with pytest.raises(ValidationError):
            ExtractedEntityDTO(text="x", type="url", start=0, end=1, confidence=1.1)


class TestEntityExtractResponse:
    """Response DTO."""

    def test_empty_response(self):
        resp = EntityExtractResponse(
            entities=[],
            tone=None,
            processing_time_ms=5,
            extractor_used="mock",
            channel="sms",
        )
        assert resp.entities == []
        assert resp.tone is None

    def test_response_with_entities(self):
        resp = EntityExtractResponse(
            entities=[
                ExtractedEntityDTO(
                    text="Sarah", type="person_name", start=0, end=5, confidence=0.9
                ),
            ],
            tone="casual",
            processing_time_ms=12,
            extractor_used="mock",
            channel="sms",
        )
        assert len(resp.entities) == 1
        assert resp.tone == "casual"
        assert resp.extractor_used == "mock"


class TestResponseShaping:
    """ExtractionResult maps correctly to EntityExtractResponse."""

    def test_shape_from_extraction_result(self):
        """ExtractionResult → EntityExtractResponse preserves all fields."""
        entity = ExtractedEntity(
            text="Sarah",
            type=EntityType.PERSON_NAME,
            start=0,
            end=5,
            confidence=0.95,
        )
        result = ExtractionResult(
            entities=[entity],
            tone=Tone.WARM,
            processing_time_ms=42,
            extractor_used="mock",
        )

        # This is the shaping logic we expect the endpoint to use
        resp = EntityExtractResponse(
            entities=[
                ExtractedEntityDTO(
                    text=e.text,
                    type=e.type.value,
                    start=e.start,
                    end=e.end,
                    confidence=e.confidence,
                )
                for e in result.entities
            ],
            tone=result.tone.value if result.tone else None,
            processing_time_ms=result.processing_time_ms,
            extractor_used=result.extractor_used,
            channel="sms",
        )

        assert resp.entities[0].text == "Sarah"
        assert resp.entities[0].type == "person_name"
        assert resp.tone == "warm"
        assert resp.processing_time_ms == 42
