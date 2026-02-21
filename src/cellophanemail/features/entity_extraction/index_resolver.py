"""IndexResolver — resolves entity text positions within content.

Uses str.find() with cursor tracking to avoid duplicate matches.
Longer-span-wins logic for overlapping text.
"""

from typing import List

from .types import EntityType, ExtractedEntity


class IndexResolver:
    """Resolves raw entity dicts (text, type, confidence) into
    ExtractedEntity objects with correct start/end positions."""

    @staticmethod
    def resolve(content: str, raw_entities: list[dict]) -> list[ExtractedEntity]:
        """Resolve entity positions within content.

        Args:
            content: The original text content.
            raw_entities: List of dicts with text, type, confidence keys.

        Returns:
            List of ExtractedEntity with correct start/end positions.
            Entities whose text is not found in content are excluded.
            When spans overlap, the longer span wins.
        """
        if not content or not raw_entities:
            return []

        # Sort by text length descending so longer spans get first pick
        sorted_raw = sorted(raw_entities, key=lambda e: len(e.get("text", "")), reverse=True)

        # Track which character positions are already claimed
        claimed: list[tuple[int, int]] = []
        resolved: list[ExtractedEntity] = []

        for raw in sorted_raw:
            text = raw.get("text", "")
            entity_type_str = raw.get("type", "")
            confidence = float(raw.get("confidence", 0.5))

            if not text:
                continue

            # Parse entity type
            try:
                entity_type = EntityType(entity_type_str)
            except ValueError:
                continue

            # Find the text in content, starting from beginning
            # For repeated substrings, find the first unclaimed occurrence
            search_start = 0
            found_start = -1

            while search_start < len(content):
                pos = content.find(text, search_start)
                if pos == -1:
                    break

                candidate_start = pos
                candidate_end = pos + len(text)

                # Check if this position overlaps with any claimed span
                overlaps = any(
                    candidate_start < ce and candidate_end > cs
                    for cs, ce in claimed
                )

                if not overlaps:
                    found_start = candidate_start
                    break

                # Try next occurrence
                search_start = pos + 1

            if found_start == -1:
                continue

            found_end = found_start + len(text)
            claimed.append((found_start, found_end))
            resolved.append(
                ExtractedEntity(
                    text=text,
                    type=entity_type,
                    start=found_start,
                    end=found_end,
                    confidence=confidence,
                )
            )

        # Sort by position for consistent output
        resolved.sort(key=lambda e: e.start)
        return resolved
