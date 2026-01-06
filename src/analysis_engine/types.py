# ABOUTME: Core types for Four Horseman analysis
# ABOUTME: Pure Pydantic models - no framework dependencies

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ThreatLevel(str, Enum):
    """Email threat level classification."""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: float) -> "ThreatLevel":
        """Derive threat level from toxicity score."""
        if score < 0.30:
            return cls.SAFE
        elif score < 0.55:
            return cls.LOW
        elif score < 0.70:
            return cls.MEDIUM
        elif score < 0.90:
            return cls.HIGH
        else:
            return cls.CRITICAL


class HorsemanDetection(BaseModel):
    """Detection of a specific horseman pattern."""

    horseman: str  # criticism, contempt, defensiveness, stonewalling
    confidence: float = Field(..., ge=0.0, le=1.0)
    indicators: List[str] = Field(default_factory=list)
    severity: str  # low, medium, high

    model_config = {"frozen": True}

    @property
    def is_significant(self) -> bool:
        """Check if detection confidence is significant."""
        return self.confidence > 0.5


class AnalysisResult(BaseModel):
    """Result of Four Horseman analysis."""

    safe: bool
    threat_level: ThreatLevel
    toxicity_score: float = Field(..., ge=0.0, le=1.0)
    horsemen_detected: List[HorsemanDetection] = Field(default_factory=list)
    reasoning: str
    processing_time_ms: int
    cached: bool = False

    model_config = {"frozen": True}

    @property
    def detected_horsemen_names(self) -> List[str]:
        """Get names of significantly detected horsemen."""
        return [h.horseman for h in self.horsemen_detected if h.is_significant]


class ProtectionResult(BaseModel):
    """Final result of protection processing."""

    should_forward: bool
    analysis: Optional[AnalysisResult] = None
    block_reason: Optional[str] = None
    message_id: str
    protection_action: Optional[str] = None
    processed_content: Optional[str] = None
    decision_reasoning: Optional[str] = None
