"""Tests for IndexResolver — RED phase.

These tests define the contract for resolving entity text positions
within a content string before any implementation exists.
"""

from cellophanemail.features.entity_extraction.types import EntityType
from cellophanemail.features.entity_extraction.index_resolver import IndexResolver


class TestIndexResolver:
    """IndexResolver.resolve() maps raw entity dicts to ExtractedEntity with positions."""

    def test_resolve_simple(self):
        """'Sarah' in 'Sarah said hello' resolves to start=0, end=5."""
        content = "Sarah said hello"
        raw = [{"text": "Sarah", "type": "person_name", "confidence": 0.9}]
        entities = IndexResolver.resolve(content, raw)
        assert len(entities) == 1
        assert entities[0].text == "Sarah"
        assert entities[0].start == 0
        assert entities[0].end == 5
        assert entities[0].type == EntityType.PERSON_NAME

    def test_resolve_multiple_entities(self):
        """Multiple entities get correct non-overlapping positions."""
        content = "Sarah met Bob at the park"
        raw = [
            {"text": "Sarah", "type": "person_name", "confidence": 0.9},
            {"text": "Bob", "type": "person_name", "confidence": 0.85},
            {"text": "the park", "type": "location", "confidence": 0.8},
        ]
        entities = IndexResolver.resolve(content, raw)
        assert len(entities) == 3

        # Verify all positions are correct
        sarah = next(e for e in entities if e.text == "Sarah")
        bob = next(e for e in entities if e.text == "Bob")
        park = next(e for e in entities if e.text == "the park")

        assert sarah.start == 0
        assert sarah.end == 5
        assert bob.start == 10
        assert bob.end == 13
        assert park.start == 17
        assert park.end == 25

    def test_resolve_repeated_substring(self):
        """'the' appears 3x, each instance resolved to different position."""
        content = "the cat sat on the mat near the door"
        raw = [
            {"text": "the cat", "type": "organization", "confidence": 0.5},
            {"text": "the mat", "type": "location", "confidence": 0.5},
            {"text": "the door", "type": "location", "confidence": 0.5},
        ]
        entities = IndexResolver.resolve(content, raw)
        assert len(entities) == 3

        positions = [(e.start, e.end) for e in entities]
        # Each should be at a different position
        assert len(set(positions)) == 3

        # Verify correct positions
        cat = next(e for e in entities if e.text == "the cat")
        mat = next(e for e in entities if e.text == "the mat")
        door = next(e for e in entities if e.text == "the door")

        assert cat.start == 0
        assert mat.start == 15
        assert door.start == 27

    def test_resolve_longer_span_wins(self):
        """'next Tuesday at 6pm' preferred over 'Tuesday' when both present."""
        content = "Meet me next Tuesday at 6pm"
        raw = [
            {"text": "Tuesday", "type": "date_time", "confidence": 0.7},
            {"text": "next Tuesday at 6pm", "type": "date_time", "confidence": 0.9},
        ]
        entities = IndexResolver.resolve(content, raw)
        # Only the longer span should survive
        assert len(entities) == 1
        assert entities[0].text == "next Tuesday at 6pm"
        assert entities[0].start == 8
        assert entities[0].end == 27

    def test_resolve_missing_text(self):
        """Entity text not found in content is excluded from results."""
        content = "Sarah said hello"
        raw = [
            {"text": "Sarah", "type": "person_name", "confidence": 0.9},
            {"text": "Chicago", "type": "location", "confidence": 0.8},
        ]
        entities = IndexResolver.resolve(content, raw)
        assert len(entities) == 1
        assert entities[0].text == "Sarah"

    def test_resolve_unicode(self):
        """Handles emoji and CJK characters correctly."""
        content = "Meet at Tokyo Tower 🗼 next week"
        raw = [
            {"text": "Tokyo Tower", "type": "location", "confidence": 0.9},
        ]
        entities = IndexResolver.resolve(content, raw)
        assert len(entities) == 1
        assert entities[0].text == "Tokyo Tower"
        assert content[entities[0].start:entities[0].end] == "Tokyo Tower"

    def test_resolve_empty_input(self):
        """Empty content and empty raw entities return empty list."""
        assert IndexResolver.resolve("", []) == []
        assert IndexResolver.resolve("hello", []) == []
        assert IndexResolver.resolve("", [{"text": "x", "type": "person_name", "confidence": 0.5}]) == []
