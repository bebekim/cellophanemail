"""RenderAST — typed Document AST for Android Compose renderer.

The server emits this AST; the Android renderer consumes it deterministically.
Style tokens are enum-only — the LLM (or deterministic compositor) picks from
enums, never raw CSS/color values. The renderer maps tokens to visual styles.

Pipeline: Text → Extractor → Entities+Tone → Compositor → RenderAST → Renderer → Compose UI
"""

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator

_SCHEMA_VERSION = 1


class BlockType(str, Enum):
    """Block types in the AST. v1: text only (SMS bubbles)."""

    TEXT = "text"


class DecorationStyle(str, Enum):
    """Style tokens for span decorations. Maps 1:1 to entity types + emphasis."""

    PERSON_NAME = "person_name"
    LOCATION = "location"
    ORGANIZATION = "organization"
    DATE_TIME = "date_time"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    EMPHASIS = "emphasis"


class EntityDecoration(BaseModel):
    """Decoration metadata for entity-highlighted spans."""

    model_config = {"frozen": True}

    entity_type: str = Field(..., description="Entity type matching DecorationStyle value")
    confidence: float = Field(..., ge=0.0, le=1.0)
    tappable: bool = Field(default=True, description="Whether span opens action sheet on tap")


class LinkDecoration(BaseModel):
    """Decoration metadata for URL/link spans."""

    model_config = {"frozen": True}

    url: str = Field(..., description="Target URL for the link")
    tappable: bool = Field(default=True)


SpanDecoration = Union[EntityDecoration, LinkDecoration]


class AnnotatedSpan(BaseModel):
    """An inline annotation within a text block.

    Represents a character range [start, end) with a style token and
    decoration metadata. The renderer uses style to pick colors/underlines
    and decoration for tap actions.
    """

    model_config = {"frozen": True}

    start: int = Field(..., ge=0, description="Start character index (inclusive)")
    end: int = Field(..., ge=0, description="End character index (exclusive)")
    style: DecorationStyle = Field(..., description="Style token for rendering")
    decoration: SpanDecoration = Field(..., description="Metadata for tap actions")

    @model_validator(mode="after")
    def end_exceeds_start(self):
        if self.end <= self.start:
            raise ValueError(f"end ({self.end}) must be greater than start ({self.start})")
        return self


class TextBlock(BaseModel):
    """A block of text with optional annotated spans."""

    model_config = {"frozen": True}

    block_type: BlockType = Field(default=BlockType.TEXT)
    text: str = Field(..., description="The full text content")
    spans: List[AnnotatedSpan] = Field(
        default_factory=list, description="Annotated spans within the text"
    )


class ToneBadge(BaseModel):
    """Tone indicator for the message — rendered as a badge/chip."""

    model_config = {"frozen": True}

    tone: Optional[str] = Field(None, description="Detected tone value")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Document(BaseModel):
    """Root AST node — the full render instruction for one message.

    This is the JSON contract between server and Android. The Android
    Compose renderer walks this tree deterministically.
    """

    model_config = {"frozen": True}

    schema_version: int = Field(..., description="AST schema version for compatibility")
    blocks: List[TextBlock] = Field(default_factory=list)
    tone: Optional[ToneBadge] = Field(default=None)

    @classmethod
    def from_extraction_result(
        cls,
        content: str,
        result: "ExtractionResult",
    ) -> "Document":
        """Build a Document from an ExtractionResult.

        This is the deterministic v1 compositor — no LLM involved.
        Maps entities to annotated spans, tone to badge.
        """
        from .types import Tone

        # Map entity type values to DecorationStyle
        style_map = {s.value: s for s in DecorationStyle}

        spans: list[AnnotatedSpan] = []
        for entity in result.entities:
            style = style_map.get(entity.type.value)
            if style is None:
                continue

            if style == DecorationStyle.URL:
                decoration: SpanDecoration = LinkDecoration(url=entity.text)
            else:
                decoration = EntityDecoration(
                    entity_type=entity.type.value,
                    confidence=entity.confidence,
                )

            spans.append(
                AnnotatedSpan(
                    start=entity.start,
                    end=entity.end,
                    style=style,
                    decoration=decoration,
                )
            )

        block = TextBlock(text=content, spans=spans)

        tone_badge: Optional[ToneBadge] = None
        if result.tone is not None:
            tone_badge = ToneBadge(tone=result.tone.value, confidence=0.8)

        return cls(
            blocks=[block],
            tone=tone_badge,
            schema_version=_SCHEMA_VERSION,
        )


# Deferred import for type checking
from .types import ExtractionResult as ExtractionResult  # noqa: E402, F401
