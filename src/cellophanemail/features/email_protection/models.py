"""Models for email protection feature."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ThreatLevel(Enum):
    """Email threat level classification."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HorsemanDetection:
    """Detection of a specific horseman."""
    horseman: str  # harassment, deception, exploitation, manipulation
    confidence: float  # 0.0 to 1.0
    indicators: List[str]  # Specific indicators found
    severity: str  # low, medium, high


@dataclass
class AnalysisResult:
    """Result of Four Horsemen analysis."""
    safe: bool
    threat_level: ThreatLevel
    toxicity_score: float  # 0.0 to 1.0
    horsemen_detected: List[HorsemanDetection]
    reasoning: str
    processing_time_ms: int
    cached: bool = False


@dataclass
class ProtectionResult:
    """Final result of email protection processing."""
    should_forward: bool
    analysis: Optional[AnalysisResult]
    block_reason: Optional[str]
    forwarded_to: Optional[List[str]]
    logged_at: datetime
    message_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "should_forward": self.should_forward,
            "threat_level": self.analysis.threat_level.value if self.analysis else None,
            "toxicity_score": self.analysis.toxicity_score if self.analysis else 0.0,
            "horsemen_detected": [
                h.horseman for h in (self.analysis.horsemen_detected if self.analysis else [])
            ],
            "block_reason": self.block_reason,
            "forwarded_to": self.forwarded_to,
            "processing_time_ms": self.analysis.processing_time_ms if self.analysis else 0,
            "cached": self.analysis.cached if self.analysis else False
        }