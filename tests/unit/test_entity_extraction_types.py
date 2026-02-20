"""Tests for entity extraction types — RED phase.

These tests define the contract for EntityType, Tone, ExtractedEntity,
and ExtractionResult before any implementation exists.
"""

import pytest
from pydantic import ValidationError

from cellophanemail.features.entity_extraction.types import (
    EntityType,
    Tone,
    ExtractedEntity,
    ExtractionResult,
)


class TestEntityTypeEnum:
    """EntityType enum must have exactly 7 values."""

    def test_entity_type_enum_values(self):
        assert EntityType.PERSON_NAME == "person_name"
        assert EntityType.LOCATION == "location"
        assert EntityType.ORGANIZATION == "organization"
        assert EntityType.DATE_TIME == "date_time"
        assert EntityType.URL == "url"
        assert EntityType.EMAIL == "email"
        assert EntityType.PHONE_NUMBER == "phone_number"

    def test_entity_type_has_exactly_7_values(self):
        assert len(EntityType) == 7


class TestToneEnum:
    """Tone enum must have exactly 5 values."""

    def test_tone_enum_values(self):
        assert Tone.WARM == "warm"
        assert Tone.FORMAL == "formal"
        assert Tone.CASUAL == "casual"
        assert Tone.CONTEMPLATIVE == "contemplative"
        assert Tone.URGENT == "urgent"

    def test_tone_has_exactly_5_values(self):
        assert len(Tone) == 5


class TestExtractedEntity:
    """ExtractedEntity is a frozen Pydantic model with validation."""

    def test_valid_entity_creates_successfully(self):
        entity = ExtractedEntity(
            text="Sarah",
            type=EntityType.PERSON_NAME,
            start=0,
            end=5,
            confidence=0.95,
        )
        assert entity.text == "Sarah"
        assert entity.type == EntityType.PERSON_NAME
        assert entity.start == 0
        assert entity.end == 5
        assert entity.confidence == 0.95

    def test_negative_start_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ExtractedEntity(
                text="Sarah",
                type=EntityType.PERSON_NAME,
                start=-1,
                end=5,
                confidence=0.95,
            )

    def test_confidence_above_1_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ExtractedEntity(
                text="Sarah",
                type=EntityType.PERSON_NAME,
                start=0,
                end=5,
                confidence=1.5,
            )

    def test_confidence_below_0_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ExtractedEntity(
                text="Sarah",
                type=EntityType.PERSON_NAME,
                start=0,
                end=5,
                confidence=-0.1,
            )

    def test_extracted_entity_frozen(self):
        entity = ExtractedEntity(
            text="Sarah",
            type=EntityType.PERSON_NAME,
            start=0,
            end=5,
            confidence=0.95,
        )
        with pytest.raises(ValidationError):
            entity.text = "Bob"


class TestExtractionResult:
    """ExtractionResult is a frozen Pydantic model."""

    def test_extraction_result_empty(self):
        result = ExtractionResult()
        assert result.entities == []
        assert result.tone is None
        assert result.processing_time_ms == 0
        assert result.extractor_used == ""

    def test_extraction_result_with_entities(self):
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
        assert len(result.entities) == 1
        assert result.tone == Tone.WARM
        assert result.processing_time_ms == 42
        assert result.extractor_used == "mock"

    def test_extraction_result_json_roundtrip(self):
        entity = ExtractedEntity(
            text="Park",
            type=EntityType.LOCATION,
            start=10,
            end=14,
            confidence=0.8,
        )
        result = ExtractionResult(
            entities=[entity],
            tone=Tone.CASUAL,
            processing_time_ms=15,
            extractor_used="anthropic",
        )
        json_str = result.model_dump_json()
        restored = ExtractionResult.model_validate_json(json_str)
        assert restored.entities[0].text == "Park"
        assert restored.entities[0].type == EntityType.LOCATION
        assert restored.tone == Tone.CASUAL
        assert restored.processing_time_ms == 15
        assert restored.extractor_used == "anthropic"
