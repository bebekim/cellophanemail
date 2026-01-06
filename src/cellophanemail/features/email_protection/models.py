"""Models for email protection feature.

Re-exports core types from analysis_engine for backwards compatibility.
Extended ProtectionResult with cellophanemail-specific fields.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

# Re-export core types from portable analysis_engine
from analysis_engine import (
    ThreatLevel,
    HorsemanDetection,
    AnalysisResult,
)

if TYPE_CHECKING:
    from .graduated_decision_maker import ProtectionAction

# Note: We keep ProtectionResult as a dataclass here because it has
# cellophanemail-specific fields (forwarded_to, logged_at, to_dict)
# that don't belong in the portable analysis_engine package.


@dataclass
class ProtectionResult:
    """Final result of email protection processing.

    Extended version with cellophanemail-specific fields.
    """
    should_forward: bool
    analysis: Optional[AnalysisResult]
    block_reason: Optional[str]
    forwarded_to: Optional[List[str]]
    logged_at: datetime
    message_id: str
    # Graduated decision fields
    protection_action: Optional['ProtectionAction'] = None
    processed_content: Optional[str] = None
    decision_reasoning: Optional[str] = None

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
            "cached": self.analysis.cached if self.analysis else False,
            # Graduated decision fields
            "protection_action": self.protection_action.value if self.protection_action else None,
            "processed_content": self.processed_content,
            "decision_reasoning": self.decision_reasoning
        }


# Re-export for backwards compatibility
__all__ = [
    "ThreatLevel",
    "HorsemanDetection",
    "AnalysisResult",
    "ProtectionResult",
]