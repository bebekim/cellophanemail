"""Tests for RenderAST Pydantic types — RED phase.

Defines the contract for the typed Document AST that the Android
Compose renderer consumes. Minimal block set for SMS message bubbles.
"""

import json

import pytest
from pydantic import ValidationError

from cellophanemail.features.entity_extraction.render_ast import (
    AnnotatedSpan,
    BlockType,
    DecorationStyle,
    Document,
    EntityDecoration,
    LinkDecoration,
    SpanDecoration,
    TextBlock,
    ToneBadge,
)


class TestBlockType:
    """Block type enum for the AST."""

    def test_text_block_type(self):
        assert BlockType.TEXT == "text"

    def test_has_exactly_expected_types(self):
        # v1: just text blocks for SMS bubbles
        assert "text" in [b.value for b in BlockType]


class TestDecorationStyle:
    """Style tokens — enum-only, no raw CSS values."""

    def test_entity_styles(self):
        assert DecorationStyle.PERSON_NAME == "person_name"
        assert DecorationStyle.LOCATION == "location"
        assert DecorationStyle.ORGANIZATION == "organization"
        assert DecorationStyle.DATE_TIME == "date_time"
        assert DecorationStyle.URL == "url"
        assert DecorationStyle.EMAIL == "email"
        assert DecorationStyle.PHONE_NUMBER == "phone_number"

    def test_emphasis_style(self):
        assert DecorationStyle.EMPHASIS == "emphasis"


class TestAnnotatedSpan:
    """Inline annotation within a text block."""

    def test_valid_span(self):
        span = AnnotatedSpan(
            start=5,
            end=10,
            style=DecorationStyle.PERSON_NAME,
            decoration=EntityDecoration(entity_type="person_name", confidence=0.95),
        )
        assert span.start == 5
        assert span.end == 10
        assert span.style == DecorationStyle.PERSON_NAME

    def test_span_rejects_negative_start(self):
        with pytest.raises(ValidationError):
            AnnotatedSpan(
                start=-1, end=5, style=DecorationStyle.URL,
                decoration=EntityDecoration(entity_type="url", confidence=0.9),
            )

    def test_span_end_must_exceed_start(self):
        with pytest.raises(ValidationError):
            AnnotatedSpan(
                start=5, end=5, style=DecorationStyle.URL,
                decoration=EntityDecoration(entity_type="url", confidence=0.9),
            )

    def test_span_frozen(self):
        span = AnnotatedSpan(
            start=0, end=5, style=DecorationStyle.PERSON_NAME,
            decoration=EntityDecoration(entity_type="person_name", confidence=0.9),
        )
        with pytest.raises(ValidationError):
            span.start = 3


class TestEntityDecoration:
    """Decoration metadata for entity-type spans."""

    def test_entity_decoration(self):
        dec = EntityDecoration(entity_type="person_name", confidence=0.95)
        assert dec.entity_type == "person_name"
        assert dec.confidence == 0.95
        assert dec.tappable is True  # entities are tappable by default

    def test_link_decoration(self):
        dec = LinkDecoration(url="https://example.com")
        assert dec.url == "https://example.com"
        assert dec.tappable is True


class TestTextBlock:
    """A block of text with optional annotated spans."""

    def test_plain_text_block(self):
        block = TextBlock(text="Hello world")
        assert block.text == "Hello world"
        assert block.spans == []
        assert block.block_type == BlockType.TEXT

    def test_annotated_text_block(self):
        span = AnnotatedSpan(
            start=0, end=5, style=DecorationStyle.PERSON_NAME,
            decoration=EntityDecoration(entity_type="person_name", confidence=0.9),
        )
        block = TextBlock(text="Sarah said hello", spans=[span])
        assert len(block.spans) == 1
        assert block.text[block.spans[0].start : block.spans[0].end] == "Sarah"

    def test_multiple_spans(self):
        block = TextBlock(
            text="Tell Sarah about https://example.com",
            spans=[
                AnnotatedSpan(
                    start=5, end=10, style=DecorationStyle.PERSON_NAME,
                    decoration=EntityDecoration(entity_type="person_name", confidence=0.9),
                ),
                AnnotatedSpan(
                    start=17, end=36, style=DecorationStyle.URL,
                    decoration=LinkDecoration(url="https://example.com"),
                ),
            ],
        )
        assert len(block.spans) == 2


class TestToneBadge:
    """Tone indicator rendered above/below the message bubble."""

    def test_tone_badge(self):
        badge = ToneBadge(tone="urgent", confidence=0.85)
        assert badge.tone == "urgent"
        assert badge.confidence == 0.85

    def test_none_tone(self):
        badge = ToneBadge(tone=None)
        assert badge.tone is None
        assert badge.confidence == 0.0


class TestDocument:
    """Root AST node — the full render instruction for one message."""

    def test_empty_document(self):
        doc = Document(blocks=[], schema_version=1)
        assert doc.blocks == []
        assert doc.schema_version == 1
        assert doc.tone is None

    def test_document_with_blocks_and_tone(self):
        block = TextBlock(text="Meet Sarah at the park")
        doc = Document(
            blocks=[block],
            tone=ToneBadge(tone="casual", confidence=0.8),
            schema_version=1,
        )
        assert len(doc.blocks) == 1
        assert doc.tone.tone == "casual"

    def test_document_json_roundtrip(self):
        """Document serializes to JSON and deserializes back identically."""
        span = AnnotatedSpan(
            start=5, end=10, style=DecorationStyle.PERSON_NAME,
            decoration=EntityDecoration(entity_type="person_name", confidence=0.95),
        )
        block = TextBlock(text="Tell Sarah hello", spans=[span])
        doc = Document(
            blocks=[block],
            tone=ToneBadge(tone="warm", confidence=0.7),
            schema_version=1,
        )

        json_str = doc.model_dump_json()
        restored = Document.model_validate_json(json_str)

        assert len(restored.blocks) == 1
        assert restored.blocks[0].text == "Tell Sarah hello"
        assert len(restored.blocks[0].spans) == 1
        assert restored.blocks[0].spans[0].style == DecorationStyle.PERSON_NAME
        assert restored.tone.tone == "warm"
        assert restored.schema_version == 1

    def test_document_schema_version_required(self):
        with pytest.raises(ValidationError):
            Document(blocks=[])

    def test_document_frozen(self):
        doc = Document(blocks=[], schema_version=1)
        with pytest.raises(ValidationError):
            doc.schema_version = 2


class TestDocumentFromExtractionResult:
    """Document can be built from ExtractionResult — the compositor bridge."""

    def test_build_from_extraction_result(self):
        """ExtractionResult maps to Document with positioned spans."""
        from cellophanemail.features.entity_extraction.types import (
            EntityType,
            ExtractionResult,
            ExtractedEntity,
            Tone,
        )

        entity = ExtractedEntity(
            text="Sarah", type=EntityType.PERSON_NAME,
            start=5, end=10, confidence=0.95,
        )
        result = ExtractionResult(
            entities=[entity], tone=Tone.WARM,
            processing_time_ms=10, extractor_used="mock",
        )

        # Build document from result
        doc = Document.from_extraction_result(
            content="Tell Sarah hello",
            result=result,
        )

        assert len(doc.blocks) == 1
        assert doc.blocks[0].text == "Tell Sarah hello"
        assert len(doc.blocks[0].spans) == 1
        assert doc.blocks[0].spans[0].start == 5
        assert doc.blocks[0].spans[0].end == 10
        assert doc.blocks[0].spans[0].style == DecorationStyle.PERSON_NAME
        assert doc.tone.tone == "warm"
        assert doc.schema_version == 1
