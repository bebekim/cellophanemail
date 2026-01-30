# ABOUTME: Protection decision logic based on Four Horsemen detection
# ABOUTME: Identical across all apps (web, Android)

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from .types import AnalysisResult, HorsemanDetection, ThreatLevel


class ProtectionAction(str, Enum):
    """Available protection actions."""

    FORWARD_CLEAN = "forward_clean"
    FORWARD_WITH_CONTEXT = "forward_with_context"
    REDACT_HARMFUL = "redact_harmful"
    SUMMARIZE_ONLY = "summarize_only"
    BLOCK_ENTIRELY = "block_entirely"


class ProtectionDecision(BaseModel):
    """Decision made by scoring logic."""

    action: ProtectionAction
    processed_content: str
    reasoning: str
    threat_level: ThreatLevel
    original_analysis: Optional[AnalysisResult] = None


def decide_action(horsemen: List[HorsemanDetection]) -> ProtectionAction:
    """
    Determine protection action based on detected horsemen.

    This is the core decision logic shared across all apps.
    Uses contempt-weighted model based on Gottman research.

    Args:
        horsemen: List of detected horsemen patterns

    Returns:
        ProtectionAction indicating how to handle the content
    """
    threat_level = ThreatLevel.from_horsemen(horsemen)

    action_map = {
        ThreatLevel.SAFE: ProtectionAction.FORWARD_CLEAN,
        ThreatLevel.LOW: ProtectionAction.FORWARD_WITH_CONTEXT,
        ThreatLevel.MEDIUM: ProtectionAction.REDACT_HARMFUL,
        ThreatLevel.HIGH: ProtectionAction.SUMMARIZE_ONLY,
        ThreatLevel.CRITICAL: ProtectionAction.BLOCK_ENTIRELY,
    }

    return action_map[threat_level]


def get_action_description(action: ProtectionAction) -> str:
    """Get human-readable description of a protection action."""
    descriptions = {
        ProtectionAction.FORWARD_CLEAN: "Forward as-is (safe content)",
        ProtectionAction.FORWARD_WITH_CONTEXT: "Forward with context notes",
        ProtectionAction.REDACT_HARMFUL: "Redact harmful content",
        ProtectionAction.SUMMARIZE_ONLY: "Provide factual summary only",
        ProtectionAction.BLOCK_ENTIRELY: "Block entirely (too toxic)",
    }
    return descriptions.get(action, "Unknown action")
