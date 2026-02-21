"""Entity extraction types — frozen Pydantic models.

Mirrors the pattern from analysis_engine types and email_protection models.
All models are frozen (immutable) for safety.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of named entities that can be extracted from text."""

    PERSON_NAME = "person_name"
    LOCATION = "location"
    ORGANIZATION = "organization"
    DATE_TIME = "date_time"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"


class Tone(str, Enum):
    """Detected tone of the message content."""

    WARM = "warm"
    FORMAL = "formal"
    CASUAL = "casual"
    CONTEMPLATIVE = "contemplative"
    URGENT = "urgent"


class ExtractedEntity(BaseModel):
    """A single named entity extracted from text with position info."""

    model_config = {"frozen": True}

    text: str = Field(..., description="The entity text as it appears in content")
    type: EntityType = Field(..., description="Classification of the entity")
    start: int = Field(..., ge=0, description="Start character index in content")
    end: int = Field(..., ge=0, description="End character index in content (exclusive)")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Extraction confidence score"
    )


class ExtractionResult(BaseModel):
    """Complete result of entity extraction from a piece of content."""

    model_config = {"frozen": True}

    entities: List[ExtractedEntity] = Field(default_factory=list)
    tone: Optional[Tone] = Field(default=None, description="Detected message tone")
    processing_time_ms: int = Field(default=0)
    extractor_used: str = Field(default="")
