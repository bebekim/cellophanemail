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
    def from_horsemen(cls, horsemen: List["HorsemanDetection"]) -> "ThreatLevel":
        """Derive threat level from detected horsemen (contempt-weighted).

        Gottman research shows contempt is the #1 predictor of relationship failure,
        so it escalates threat level immediately.

        Logic:
        - SAFE: No significant horsemen detected
        - LOW: Single non-contempt horseman
        - MEDIUM: 2 non-contempt horsemen, OR criticism + defensiveness
        - HIGH: Contempt detected, OR 3+ non-contempt horsemen
        - CRITICAL: Contempt + any other horseman, OR all 4 horsemen
        """
        significant = [h for h in horsemen if h.is_significant]
        types = {h.horseman for h in significant}

        if not significant:
            return cls.SAFE

        has_contempt = "contempt" in types

        if has_contempt:
            return cls.CRITICAL if len(types) > 1 else cls.HIGH

        if len(types) >= 4:
            return cls.CRITICAL

        if len(types) >= 3:
            return cls.HIGH

        if len(types) == 2:
            return cls.MEDIUM

        return cls.LOW


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
    horsemen_detected: List[HorsemanDetection] = Field(default_factory=list)
    reasoning: str
    processing_time_ms: int
    cached: bool = False

    model_config = {"frozen": True}

    @property
    def detected_horsemen_names(self) -> List[str]:
        """Get names of significantly detected horsemen."""
        return [h.horseman for h in self.horsemen_detected if h.is_significant]

    @property
    def is_toxic(self) -> bool:
        """Check if content is considered toxic based on threat level."""
        return self.threat_level != ThreatLevel.SAFE


class ProtectionResult(BaseModel):
    """Final result of protection processing."""

    should_forward: bool
    analysis: Optional[AnalysisResult] = None
    block_reason: Optional[str] = None
    message_id: str
    protection_action: Optional[str] = None
    processed_content: Optional[str] = None
    decision_reasoning: Optional[str] = None
